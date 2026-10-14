import ast
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from pycharm_project_at2 import at2

MODULE_PATH = "pycharm_project_at2.at2"


class AT2Tests(unittest.TestCase):
    def testSanitizeRemovesLineBreaksAndWhitespace(self):
        self.assertEqual(at2.sanitize("  first\nsecond\r  "), "first second")

    def testSanitizePreventsSpreadsheetFormulaInjection(self):
        self.assertEqual(at2.sanitize("=SUM(A1:A2)"), "'=SUM(A1:A2)")
        self.assertEqual(at2.sanitize("+cmd"), "'+cmd")
        self.assertEqual(at2.sanitize("-1"), "'-1")
        self.assertEqual(at2.sanitize("@value"), "'@value")

    @patch(f"{MODULE_PATH}.uuid.getnode", return_value=0xAABBCCDDEEFF)
    def testGetMACAddressUsesExpectedFormat(self, mockGetNode):
        self.assertEqual(at2.getMACAddress(), "AA-BB-CC-DD-EE-FF")
        mockGetNode.assert_called_once_with()

    @patch(f"{MODULE_PATH}.urllib.request.urlopen")
    @patch(f"{MODULE_PATH}.time.time", side_effect=[100.0, 101.0])
    def testGetInternetSpeedUsesHttpsRequest(self, mockTime, mockUrlOpen):
        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, excType, exc, tb):
                return False

            def read(self, _size):
                return b"x" * (1024 * 512)

        mockUrlOpen.return_value = _FakeResponse()

        at2.getInternetSpeed()

        requestArgument = mockUrlOpen.call_args[0][0]
        self.assertTrue(requestArgument.full_url.startswith("https://"))

    @patch(f"{MODULE_PATH}.subprocess.check_output", side_effect=RuntimeError("netstat error"))
    @patch(f"{MODULE_PATH}.platform.system", return_value="Linux")
    def testGetActivePortsReportsCollectionFailure(self, mockSystem, mockCheckOutput):
        capturedOutput = io.StringIO()
        with contextlib.redirect_stdout(capturedOutput):
            result = at2.getActivePorts()

        self.assertEqual(result, "")
        self.assertIn("Active port collection failed", capturedOutput.getvalue())

    @patch(f"{MODULE_PATH}.getActivePorts", return_value="80;443")
    @patch(f"{MODULE_PATH}.getInternetSpeed", return_value="25Mb/s")
    @patch(f"{MODULE_PATH}.getSystemTime", return_value="01/01/2026 09:00:00")
    @patch(f"{MODULE_PATH}.getOS", return_value="Linux 6")
    @patch(f"{MODULE_PATH}.getProcessor", return_value="CPU X")
    @patch(f"{MODULE_PATH}.getMACAddress", return_value="AA-BB-CC-DD-EE-FF")
    @patch(f"{MODULE_PATH}.getIPAddress", return_value="192.168.1.50")
    @patch(f"{MODULE_PATH}.getComputerName", return_value="PC-TEST")
    def testMainStopsAfterCsvReadFailure(
        self,
        mockComputer,
        mockIp,
        mockMac,
        mockProcessor,
        mockOs,
        mockTime,
        mockSpeed,
        mockPorts,
    ):
        previousDirectory = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tempDirectory:
                os.chdir(tempDirectory)
                with open("assets_audit.csv", "wb") as brokenCsv:
                    brokenCsv.write(b"\xff")

                capturedOutput = io.StringIO()
                with contextlib.redirect_stdout(capturedOutput):
                    at2.main()

                self.assertIn("Error reading CSV", capturedOutput.getvalue())
                self.assertNotIn("Audit complete", capturedOutput.getvalue())

                with open("assets_audit.csv", "rb") as resultFile:
                    self.assertEqual(resultFile.read(), b"\xff")
        finally:
            os.chdir(previousDirectory)

    def testFunctionsUseCamelCaseNames(self):
        sourceCode = Path("src/pycharm_project_at2/at2.py").read_text(encoding="utf-8")
        syntaxTree = ast.parse(sourceCode)
        functionNames = [
            node.name
            for node in ast.walk(syntaxTree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        invalidNames = [name for name in functionNames if "_" in name]

        self.assertEqual(invalidNames, [])

    @patch(f"{MODULE_PATH}.urllib.request.urlopen")
    @patch(f"{MODULE_PATH}.time.time", side_effect=[100.0, 101.0, 102.0])
    def testGetInternetSpeedFallsBackToSecondUrl(self, mockTime, mockUrlOpen):
        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, excType, exc, tb):
                return False

            def read(self, _size):
                return b"x" * (1024 * 512)

        mockUrlOpen.side_effect = [OSError("primary failed"), _FakeResponse()]

        result = at2.getInternetSpeed()

        self.assertEqual(result, "4Mb/s")
        self.assertEqual(mockUrlOpen.call_count, 2)

    @patch(f"{MODULE_PATH}.platform.system", return_value="Linux")
    @patch(f"{MODULE_PATH}.subprocess.check_output")
    def testGetActivePortsFallsBackToNetstatOnLinux(self, mockCheckOutput, mockSystem):
        ssError = FileNotFoundError("ss not found")
        netstatOutput = (
            "Proto Recv-Q Send-Q Local Address           Foreign Address         State\n"
            "tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN\n"
            "tcp6       0      0 :::443                  :::*                    LISTEN\n"
        ).encode("utf-8")
        mockCheckOutput.side_effect = [ssError, netstatOutput]

        result = at2.getActivePorts()

        self.assertEqual(result, "22;443")


if __name__ == "__main__":
    unittest.main()
