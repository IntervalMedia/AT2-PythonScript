"""Collect local asset details and maintain the shared audit CSV."""

import csv
import datetime
import ipaddress
import os
import platform
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path


COMMAND_TIMEOUT_SECONDS = 5
WINDOWS_TCP_LISTENERS = (
    "$ErrorActionPreference = 'Stop'; "
    "[System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()"
    ".GetActiveTcpListeners() | Select-Object -ExpandProperty Port"
)
AUDIT_HEADINGS = [
    "Computer Name",
    "IP address",
    "MAC address",
    "Processor Model",
    "Operation System",
    "System time",
    "Internet connection speed",
    "Active ports",
]


def sanitize(value):
    # Sanitize data to prevent CSV injection and formatting errors.
    cleanValue = str(value).replace("\n", " ").replace("\r", "").strip()
    if cleanValue.startswith(("=", "+", "-", "@")):
        return f"'{cleanValue}"
    return cleanValue


def getComputerName():
    return platform.node()


def usableIPv4(value):
    address = ipaddress.IPv4Address(value)
    if address.is_loopback or address.is_unspecified:
        raise ValueError("A network IPv4 address is unavailable.")
    return str(address)


def getIPAddress():
    """Get the routed IPv4 address, then try local hostname resolution."""
    try:
        # Connect to an external address to determine the primary routable IP.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as networkSocket:
            networkSocket.connect(("8.8.8.8", 80))
            return usableIPv4(networkSocket.getsockname()[0])
    except (OSError, ValueError):
        pass

    try:
        return usableIPv4(socket.gethostbyname(platform.node()))
    except (OSError, ValueError):
        print("[WARNING] IP address could not be determined.")
        return "Unavailable"


def getMACAddress():
    try:
        macAddress = uuid.getnode()
        hexadecimalAddress = f"{macAddress:012X}"

        # Format the address to match the assignment brief.
        addressParts = [
            hexadecimalAddress[index:index + 2]
            for index in range(0, 12, 2)
        ]
        return "-".join(addressParts).upper()
    except Exception:
        return "Unknown"


def readCommandOutput(command):
    """Run a system command without a shell and return its decoded output."""
    output = subprocess.check_output(
        command, timeout=COMMAND_TIMEOUT_SECONDS, env={**os.environ, "LC_ALL": "C"}
    )
    encoding = "utf-16" if output.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    return output.decode(encoding, errors="replace")


def readProcessorModel(operatingSystem):
    """Return a processor model from the operating system command, if present."""
    if operatingSystem == "Windows":
        output = readCommandOutput(["wmic", "cpu", "get", "name"])
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if len(lines) > 1 and lines[0].casefold() == "name":
            return lines[1]

    if operatingSystem == "Linux":
        output = readCommandOutput(["cat", "/proc/cpuinfo"])
        for line in output.splitlines():
            label, _, value = line.partition(":")
            if label.strip() == "model name" and value.strip():
                return value.strip()
    return ""


def getProcessor():
    """Fall back to a generic processor description or an unknown value."""
    operatingSystem = platform.system()
    try:
        model = readProcessorModel(operatingSystem)
        if model:
            return model
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        if operatingSystem == "Windows":
            genericModel = platform.processor().strip()
        else:
            # The generic platform lookup can launch uname on Unix.
            genericModel = readCommandOutput(
                [sys.executable, "-I", "-c", "import platform; print(platform.processor())"]
            ).strip()
        return genericModel if genericModel.casefold() not in ("", "unknown") else "Unknown"
    except Exception:
        return "Unknown"


def getOS():
    return f"{platform.system()} {platform.release()}"


def getSystemTime():
    # Format the time to display dd/mm/yyyy hh:mm:ss.
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def measureDownloadSpeed(testUrl):
    startTime = time.time()
    request = urllib.request.Request(
        testUrl,
        headers={"User-Agent": "Mozilla/5.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        # Read 512 KB from the test file.
        data = response.read(1024 * 512)
    endTime = time.time()

    duration = endTime - startTime
    if duration == 0:
        return "Unknown"

    speedBitsPerSecond = (len(data) * 8) / duration
    speedMegabitsPerSecond = speedBitsPerSecond / 1_000_000
    return f"{int(speedMegabitsPerSecond)}Mb/s"


def getInternetSpeed():
    # Estimate download speed without third-party tools.
    testUrls = [
        "https://speedtest.ftp.otenet.gr/files/test1Mb.db",
        "https://speed.cloudflare.com/__down?bytes=1000000",
    ]
    for testUrl in testUrls:
        try:
            return measureDownloadSpeed(testUrl)
        except Exception:
            continue

    return "Unknown (Offline)"


def parsePortNumber(portText):
    if len(portText) <= 5 and portText.isascii() and portText.isdecimal():
        port = int(portText)
        if 1 <= port <= 65535:
            return port
    return None


def extractPortFromAddress(addressValue):
    _, separator, portText = addressValue.rpartition(":")
    return parsePortNumber(portText) if separator else None


def parseListeningPorts(commandOutput, source="ss"):
    """Extract local listening TCP ports from the given command's columns."""
    ports = set()

    for line in commandOutput.splitlines():
        if source == "PowerShell":
            port = parsePortNumber(line.strip())
            if port is not None:
                ports.add(port)
            continue

        parts = line.split()
        if source == "Windows":
            if len(parts) < 4 or parts[0] != "TCP" or parts[3] not in ("LISTEN", "LISTENING"):
                continue
            localAddress = parts[1]
        elif source == "netstat":
            if len(parts) < 6 or parts[0] not in ("tcp", "tcp6") or parts[5] != "LISTEN":
                continue
            localAddress = parts[3]
        else:
            # Depending on the ss version the optional protocol column may appear.
            if parts and parts[0] in ("tcp", "tcp6"):
                parts = parts[1:]
            if len(parts) < 5 or parts[0] != "LISTEN":
                continue
            localAddress = parts[3]

        port = extractPortFromAddress(localAddress)
        if port is not None:
            ports.add(port)

    return ports


def getActivePorts():
    """Return sorted, distinct local listening TCP ports on Windows or Linux."""
    operatingSystem = platform.system()
    if operatingSystem == "Windows":
        commands = [
            (["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_TCP_LISTENERS],
             "PowerShell"),
            (["netstat", "-an"], "Windows"),
        ]
    elif operatingSystem == "Linux":
        commands = [(["ss", "-lntH"], "ss"), (["netstat", "-lnt"], "netstat")]
    else:
        return ""

    for command, source in commands:
        try:
            ports = parseListeningPorts(readCommandOutput(command), source)
            return ";".join(str(port) for port in sorted(ports))
        except (OSError, subprocess.SubprocessError) as error:
            lastError = error

    print(f"[WARNING] Active port collection failed: {lastError}")
    return ""


def readAuditRows(csvFile):
    """Yield validated and sanitised saved data rows in their original order."""
    try:
        csvInput = csvFile.open(newline="", encoding="utf-8-sig")
    except FileNotFoundError:
        return

    with csvInput:
        reader = csv.reader(csvInput, strict=True)
        if next(reader, None) != AUDIT_HEADINGS:
            raise ValueError("Audit headings do not match the expected eight columns.")

        for row in reader:
            if not row:
                continue
            if len(row) != len(AUDIT_HEADINGS) or not row[0].strip():
                raise ValueError(
                    f"Invalid audit row ending on line {reader.line_num}. "
                    "Expected eight fields and a computer name."
                )
            yield [sanitize(value) for value in row]


def prepareAuditRows(savedRows, currentData):
    """Merge the current record and retain one row per computer name."""
    rows = []
    seenNames = set()
    currentName = currentData[0].casefold()
    status = f"[INFO] New computer detected. Adding {currentData[0]} to CSV."

    for row in savedRows:
        savedName = row[0].casefold()
        if savedName in seenNames:
            print(f"[WARNING] Duplicate computer record ignored: {row[0]}")
            continue
        seenNames.add(savedName)

        if savedName == currentName:
            # Exclude the system time because it always changes.
            if row[1:5] + row[6:] == currentData[1:5] + currentData[6:]:
                status = (
                    f"[INFO] Computer {currentData[0]} already exists in the CSV. "
                    "No configuration changes detected."
                )
            else:
                status = (
                    f"[WARNING] Information for {currentData[0]} is already present "
                    "in the CSV file but differs from the current scan. Data updated."
                )
            rows.append(currentData)
        else:
            rows.append(row)

    if currentName not in seenNames:
        rows.append(currentData)
    return rows, status


def saveAudit(csvFile, rows):
    """Replace the audit only after its temporary copy is written and closed."""
    temporaryPath = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=csvFile.parent,
            prefix=f".{csvFile.name}.",
            suffix=".tmp",
            newline="",
            encoding="utf-8",
            delete=False,
        ) as csvOutput:
            temporaryPath = Path(csvOutput.name)
            writer = csv.writer(csvOutput)
            writer.writerow(AUDIT_HEADINGS)
            writer.writerows(rows)
            csvOutput.flush()
            os.fsync(csvOutput.fileno())

        os.replace(temporaryPath, csvFile)
        temporaryPath = None
    finally:
        if temporaryPath is not None:
            try:
                temporaryPath.unlink(missing_ok=True)
            except OSError as error:
                print(f"[WARNING] Could not remove the temporary audit file: {error}")


def main():
    """Collect asset details, validate the existing audit and save the update."""
    csvFile = Path("assets_audit.csv")
    print("Collecting system information...")
    currentData = [
        sanitize(getComputerName()),
        sanitize(getIPAddress()),
        sanitize(getMACAddress()),
        sanitize(getProcessor()),
        sanitize(getOS()),
        sanitize(getSystemTime()),
        sanitize(getInternetSpeed()),
        sanitize(getActivePorts()),
    ]

    if not currentData[0]:
        print("Error collecting audit data: The computer name is blank.")
        return

    try:
        rows, status = prepareAuditRows(readAuditRows(csvFile), currentData)
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error reading CSV: {error}")
        return

    try:
        saveAudit(csvFile, rows)
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error writing to CSV: {error}")
        return

    print(f"\n{status}")
    print(f"Audit complete. Data safely written to {csvFile}")


if __name__ == "__main__":
    main()
