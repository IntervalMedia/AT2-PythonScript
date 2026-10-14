import contextlib
import csv
import io
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_at2 import at2


HEADINGS = [
    "Computer Name", "IP address", "MAC address", "Processor Model",
    "Operation System", "System time", "Internet connection speed", "Active ports",
]
CURRENT = [
    "PC-TEST", "192.168.1.50", "AA-BB-CC-DD-EE-FF", "CPU X",
    "Linux 6", "19/11/2026 09:00:00", "25Mb/s", "80;443",
]
COLLECTORS = (
    "getComputerName", "getIPAddress", "getMACAddress", "getProcessor",
    "getOS", "getSystemTime", "getInternetSpeed", "getActivePorts",
)


class AuditCSVTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.audit = self.directory / "assets_audit.csv"
        previousDirectory = Path.cwd()
        os.chdir(self.directory)
        self.addCleanup(os.chdir, previousDirectory)
        for collector, value in zip(COLLECTORS, CURRENT):
            self.enterContext(patch.object(at2, collector, return_value=value))

    def writeRows(self, rows, encoding="utf-8"):
        with self.audit.open("w", newline="", encoding=encoding) as output:
            csv.writer(output).writerows(rows)

    def readRows(self):
        with self.audit.open(newline="", encoding="utf-8") as source:
            return list(csv.reader(source))

    def runAudit(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            at2.main()
        return output.getvalue()

    def testInvalidCSVIsReportedAndPreserved(self):
        heading = ",".join(HEADINGS).encode()
        invalidInputs = {
            "empty file": b"",
            "wrong headings": heading.replace(b"Computer Name", b"Unexpected"),
            "short data row": heading + b"\nPC-OTHER,192.0.2.10\n",
            "extra field": heading + b"\nPC-OTHER,,,,,,,,extra\n",
            "blank computer name": heading + b"\n  ,,,,,,,\n",
            "broken CSV quoting": heading + b'\n"PC-OTHER,,,,,,,',
            "invalid encoding": heading + b"\n\xff",
        }
        for problem, original in invalidInputs.items():
            with self.subTest(problem=problem):
                self.audit.write_bytes(original)

                output = self.runAudit()

                self.assertIn("Error reading CSV", output)
                self.assertNotIn("Audit complete", output)
                self.assertEqual(self.audit.read_bytes(), original)

    def testBlankCollectedNameDoesNotCreateAnAudit(self):
        with patch.object(at2, "getComputerName", return_value="   "):
            output = self.runAudit()

        self.assertIn("computer name", output.lower())
        self.assertFalse(self.audit.exists())

    def testRetainedRowsAreSanitisedAndBlankLinesAreSkipped(self):
        otherRecord = ["PC-OTHER", *CURRENT[1:]]
        dirtyRecord = [*otherRecord[:3], "  =formula\nvalue ", *otherRecord[4:]]
        cleanRecord = [*otherRecord[:3], "'=formula value", *otherRecord[4:]]
        self.writeRows([HEADINGS, [], dirtyRecord], encoding="utf-8-sig")

        self.assertIn("New computer detected", self.runAudit())
        self.assertEqual(self.readRows(), [HEADINGS, cleanRecord, CURRENT])

    def testDuplicateNamesKeepOneRowPerComputer(self):
        oldCurrent = ["pc-test", *CURRENT[1:5], "Earlier time", *CURRENT[6:]]
        duplicateCurrent = [CURRENT[0], "192.0.2.20", *CURRENT[2:]]
        firstOther = ["PC-OTHER", *CURRENT[1:]]
        duplicateOther = ["pc-other", "192.0.2.21", *CURRENT[2:]]
        self.writeRows([HEADINGS, firstOther, oldCurrent, duplicateOther, duplicateCurrent])

        output = self.runAudit()

        self.assertEqual(self.readRows(), [HEADINGS, firstOther, CURRENT])
        self.assertEqual(output.lower().count("duplicate"), 2)
        self.assertIn("No configuration changes detected", output)
        self.assertNotIn("differs from the current scan", output)

    def testChangedConfigurationReplacesSavedRecord(self):
        previous = [CURRENT[0], "192.0.2.20", *CURRENT[2:]]
        self.writeRows([HEADINGS, previous])

        self.assertIn("differs from the current scan", self.runAudit())
        self.assertEqual(self.readRows(), [HEADINGS, CURRENT])

    def testHeaderOnlyAuditAcceptsNewComputer(self):
        self.writeRows([HEADINGS])

        self.assertIn("New computer detected", self.runAudit())
        self.assertEqual(self.readRows(), [HEADINGS, CURRENT])

    def testReplacementUsesCompleteClosedTemporaryFileInSameDirectory(self):
        self.writeRows([HEADINGS])
        original = self.audit.read_bytes()
        realReplace = os.replace
        realTemporaryFile = tempfile.NamedTemporaryFile
        temporaryFiles = []

        def captureTemporaryFile(*args, **kwargs):
            temporaryFile = realTemporaryFile(*args, **kwargs)
            temporaryFiles.append(temporaryFile)
            return temporaryFile

        def checkReplacement(source, destination):
            temporaryPath = Path(source)
            self.assertEqual(temporaryPath.resolve().parent, self.directory.resolve())
            self.assertNotEqual(temporaryPath.resolve(), self.audit.resolve())
            self.assertEqual(Path(destination).resolve(), self.audit.resolve())
            self.assertTrue(temporaryFiles[0].closed)
            self.assertEqual(self.audit.read_bytes(), original)
            with temporaryPath.open(newline="", encoding="utf-8") as content:
                self.assertEqual(list(csv.reader(content)), [HEADINGS, CURRENT])
            realReplace(source, destination)

        with (
            patch.object(tempfile, "NamedTemporaryFile", side_effect=captureTemporaryFile),
            patch.object(at2.os, "replace", side_effect=checkReplacement) as replace,
        ):
            output = self.runAudit()

        replace.assert_called_once()
        self.assertIn("Audit complete", output)
        self.assertEqual(self.readRows(), [HEADINGS, CURRENT])
        self.assertEqual(list(self.directory.iterdir()), [self.audit])

    def testFirstAuditCreatesCSVWithAtomicReplacement(self):
        with patch.object(at2.os, "replace", wraps=os.replace) as replace:
            output = self.runAudit()

        replace.assert_called_once()
        self.assertIn("New computer detected", output)
        self.assertEqual(self.readRows(), [HEADINGS, CURRENT])

    def testPartialWriteFailureDoesNotReplaceOriginal(self):
        self.writeRows([HEADINGS, ["PC-OTHER", *CURRENT[1:]]])
        original = self.audit.read_bytes()
        realWriter = csv.writer

        class InterruptedWriter:
            def __init__(self, outputFile):
                self.writer = realWriter(outputFile)

            def writerow(self, row):
                self.writer.writerow(row)

            def writerows(self, rows):
                self.writer.writerow(next(iter(rows)))
                raise OSError("simulated disk full")

        with (
            patch.object(at2.csv, "writer", side_effect=InterruptedWriter),
            patch.object(at2.os, "replace", wraps=os.replace) as replace,
        ):
            output = self.runAudit()

        replace.assert_not_called()
        self.assertIn("Error writing to CSV", output)
        self.assertNotIn("Audit complete", output)
        self.assertEqual(self.audit.read_bytes(), original)
        self.assertEqual(list(self.directory.iterdir()), [self.audit])

    def testSyncFailureDoesNotReplaceOriginal(self):
        self.writeRows([HEADINGS])
        original = self.audit.read_bytes()
        with (
            patch.object(at2.os, "fsync", side_effect=OSError("sync failed")),
            patch.object(at2.os, "replace", wraps=os.replace) as replace,
        ):
            output = self.runAudit()

        replace.assert_not_called()
        self.assertIn("Error writing to CSV", output)
        self.assertNotIn("New computer detected", output)
        self.assertEqual(self.audit.read_bytes(), original)
        self.assertEqual(list(self.directory.iterdir()), [self.audit])

    def testReplaceFailurePreservesOriginalAndRemovesTemporaryFile(self):
        self.writeRows([HEADINGS])
        original = self.audit.read_bytes()
        with patch.object(at2.os, "replace", side_effect=PermissionError("CSV is open")):
            output = self.runAudit()

        self.assertIn("Error writing to CSV", output)
        self.assertNotIn("Audit complete", output)
        self.assertEqual(self.audit.read_bytes(), original)
        self.assertEqual(list(self.directory.iterdir()), [self.audit])


class SystemCollectorTests(unittest.TestCase):
    def testPrimaryIPUsesSocketAddress(self):
        with (
            patch.object(at2.socket, "socket") as createSocket,
            patch.object(at2.socket, "gethostbyname") as resolve,
        ):
            networkSocket = createSocket.return_value.__enter__.return_value
            networkSocket.getsockname.return_value = ("192.0.2.10", 12345)
            self.assertEqual(at2.getIPAddress(), "192.0.2.10")
            resolve.assert_not_called()

    def testHostnameResolutionIsUsedWhenPrimaryIPFails(self):
        with (
            patch.object(at2.socket, "socket", side_effect=OSError("no route")),
            patch.object(at2.platform, "node", return_value="PC-TEST"),
            patch.object(at2.socket, "gethostbyname", return_value="192.0.2.11") as resolve,
        ):
            self.assertEqual(at2.getIPAddress(), "192.0.2.11")
            resolve.assert_called_once_with("PC-TEST")

    def testBothIPLookupsFailWithWarningAndUnavailableValue(self):
        output = io.StringIO()
        with (
            patch.object(at2.socket, "socket", side_effect=OSError("no route")),
            patch.object(at2.socket, "gethostbyname", side_effect=socket.gaierror("DNS failed")),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(at2.getIPAddress(), "Unavailable")

        self.assertIn("[WARNING]", output.getvalue())
        self.assertIn("IP address", output.getvalue())

    def testLoopbackAndUnspecifiedAddressesAreUnavailable(self):
        for hostnameAddress in ("127.0.1.1", "0.0.0.0"):
            output = io.StringIO()
            with (
                self.subTest(address=hostnameAddress),
                patch.object(at2.socket, "socket") as createSocket,
                patch.object(at2.socket, "gethostbyname", return_value=hostnameAddress),
                contextlib.redirect_stdout(output),
            ):
                networkSocket = createSocket.return_value.__enter__.return_value
                networkSocket.getsockname.return_value = ("0.0.0.0", 0)
                self.assertEqual(at2.getIPAddress(), "Unavailable")
                self.assertIn("[WARNING]", output.getvalue())

    def testProcessorCommandsReadTheirModelWithATimeout(self):
        cases = [
            ("Windows", "\r\nName\r\n  CPU Windows  \r\n".encode("utf-16"), "CPU Windows"),
            ("Linux", b"processor : 0\nmodel name : CPU Linux\n", "CPU Linux"),
        ]
        for system, commandOutput, model in cases:
            with (
                self.subTest(system=system),
                patch.object(at2.platform, "system", return_value=system),
                patch.object(at2.platform, "processor") as generic,
                patch.object(at2.subprocess, "check_output", return_value=commandOutput) as command,
            ):
                self.assertEqual(at2.getProcessor(), model)
                generic.assert_not_called()
                self.assertEqual(command.call_args.kwargs.get("timeout"), 5)

    def testProcessorCommandFailureFallsBackToGenericModel(self):
        for system in ("Windows", "Linux"):
            for error in (
                FileNotFoundError("missing"),
                subprocess.CalledProcessError(1, ["cpu-tool"]),
                subprocess.TimeoutExpired(["cpu-tool"], 5),
            ):
                results = error if system == "Windows" else [error, b" Generic CPU \n"]
                with (
                    self.subTest(system=system, error=type(error).__name__),
                    patch.object(at2.platform, "system", return_value=system),
                    patch.object(at2.platform, "processor", return_value="  Generic CPU  "),
                    patch.object(at2.subprocess, "check_output", side_effect=results) as command,
                ):
                    self.assertEqual(at2.getProcessor(), "Generic CPU")
                    self.assertTrue(all(call.kwargs.get("timeout") == 5 for call in command.call_args_list))
                    if system == "Linux":
                        self.assertEqual(command.call_args.args[0][:2], [sys.executable, "-I"])
                        self.assertIn("platform.processor()", command.call_args.args[0][-1])

    def testMissingProcessorModelsReturnUnknown(self):
        for system, commandOutputs in (
            ("Windows", [b"Name\r\n\r\n"]),
            ("Linux", [b"model name:\n", b"unknown\n"]),
        ):
            with (
                self.subTest(system=system),
                patch.object(at2.platform, "system", return_value=system),
                patch.object(at2.platform, "processor", return_value=" "),
                patch.object(at2.subprocess, "check_output", side_effect=commandOutputs),
            ):
                self.assertEqual(at2.getProcessor(), "Unknown")

    def testGenericProcessorFailureReturnsUnknown(self):
        with (
            patch.object(at2.platform, "system", return_value="Windows"),
            patch.object(at2.platform, "processor", side_effect=OSError("CPU unavailable")),
            patch.object(at2.subprocess, "check_output", side_effect=FileNotFoundError()),
        ):
            self.assertEqual(at2.getProcessor(), "Unknown")

    def testLinuxGenericProcessorTimeoutReturnsUnknown(self):
        with (
            patch.object(at2.platform, "system", return_value="Linux"),
            patch.object(at2.subprocess, "check_output", side_effect=[
                FileNotFoundError("cat"),
                subprocess.TimeoutExpired([sys.executable], 5),
            ]) as command,
        ):
            self.assertEqual(at2.getProcessor(), "Unknown")

        self.assertEqual(command.call_count, 2)
        self.assertEqual(command.call_args.kwargs.get("timeout"), 5)

    def testWindowsAndLinuxSaveTheSameListeningTCPPorts(self):
        windows = b"443\r\n22\r\n22\r\n0\r\n65536\r\n"
        linux = b"""
tcp   LISTEN 0 511 [::]:443        [::]:*
      LISTEN 0 128 0.0.0.0:22      0.0.0.0:*
tcp   LISTEN 0 128 [::]:22         [::]:*
tcp   ESTAB  0 0   192.0.2.1:123   192.0.2.2:654
udp   UNCONN 0 0   0.0.0.0:53      0.0.0.0:*
tcp   LISTEN 0 128 0.0.0.0:*       192.0.2.2:456
"""
        cases = [
            ("Windows", windows, "powershell.exe"),
            ("Linux", linux, "ss"),
        ]
        for system, commandOutput, expectedCommand in cases:
            with (
                self.subTest(system=system),
                patch.object(at2.platform, "system", return_value=system),
                patch.object(at2.subprocess, "check_output", return_value=commandOutput) as command,
            ):
                self.assertEqual(at2.getActivePorts(), "22;443")
                command.assert_called_once()
                self.assertEqual(command.call_args.args[0][0], expectedCommand)
                if system == "Windows":
                    self.assertIn("GetActiveTcpListeners()", command.call_args.args[0][-1])
                self.assertEqual(command.call_args.kwargs.get("timeout"), 5)

    def testWindowsPowerShellTimeoutUsesLocalTCPListenersFromNetstat(self):
        netstat = b"""
  TCP  [::]:443       [::]:0               LISTENING
  TCP  0.0.0.0:22     0.0.0.0:0            LISTENING
  TCP  [::]:22        [::]:0               LISTENING
  TCP  192.0.2.1:123  192.0.2.2:654       ESTABLISHED
  UDP  0.0.0.0:53     *:*
  TCP  0.0.0.0:*      192.0.2.2:456       LISTENING
"""
        with (
            patch.object(at2.platform, "system", return_value="Windows"),
            patch.object(at2.subprocess, "check_output", side_effect=[
                subprocess.TimeoutExpired(["powershell.exe"], 5), netstat,
            ]) as command,
        ):
            self.assertEqual(at2.getActivePorts(), "22;443")

        self.assertEqual(command.call_args.args[0], ["netstat", "-an"])
        self.assertEqual([call.kwargs.get("timeout") for call in command.call_args_list], [5, 5])

    def testLinuxPortCommandTimeoutFallsBackToListeningTCPNetstat(self):
        netstat = b"""
tcp  0 0  0.0.0.0:22     0.0.0.0:*       LISTEN
tcp6 0 0  :::443         :::*            LISTEN
tcp  0 0  192.0.2.1:456  192.0.2.2:123   ESTABLISHED
udp  0 0  0.0.0.0:53     0.0.0.0:*
"""
        with (
            patch.object(at2.platform, "system", return_value="Linux"),
            patch.object(
                at2.subprocess, "check_output",
                side_effect=[subprocess.TimeoutExpired(["ss"], 5), netstat],
            ) as command,
        ):
            self.assertEqual(at2.getActivePorts(), "22;443")

        self.assertEqual([call.args[0] for call in command.call_args_list], [
            ["ss", "-lntH"], ["netstat", "-lnt"],
        ])
        self.assertEqual([call.kwargs.get("timeout") for call in command.call_args_list], [5, 5])
        self.assertEqual(command.call_args.kwargs.get("env", {}).get("LC_ALL"), "C")

    def testWindowsPortTimeoutWarnsAndReturnsEmptyField(self):
        output = io.StringIO()
        with (
            patch.object(at2.platform, "system", return_value="Windows"),
            patch.object(at2.subprocess, "check_output", side_effect=subprocess.TimeoutExpired(["netstat"], 5)),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(at2.getActivePorts(), "")

        self.assertIn("Active port collection failed", output.getvalue())

    def testSuccessfulEmptyLinuxPortOutputDoesNotRunFallback(self):
        with (
            patch.object(at2.platform, "system", return_value="Linux"),
            patch.object(at2.subprocess, "check_output", return_value=b"") as command,
        ):
            self.assertEqual(at2.getActivePorts(), "")
            command.assert_called_once()
