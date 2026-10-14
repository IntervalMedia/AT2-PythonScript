import csv
import datetime
import os
import platform
import socket
import subprocess
import time
import urllib.request
import uuid


def sanitize(value):
    # Sanitize data to prevent CSV injection and formatting errors.
    cleanValue = str(value).replace("\n", " ").replace("\r", "").strip()
    if cleanValue.startswith(("=", "+", "-", "@")):
        return f"'{cleanValue}"
    return cleanValue


def getComputerName():
    return platform.node()


def getIPAddress():
    try:
        # Connect to an external address to determine the primary routable IP.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as networkSocket:
            networkSocket.connect(("8.8.8.8", 80))
            return networkSocket.getsockname()[0]
    except Exception:
        # Fall back to local hostname resolution.
        return socket.gethostbyname(platform.node())


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


def getProcessor():
    try:
        operatingSystem = platform.system()
        if operatingSystem == "Windows":
            # Query WMI without using shell execution.
            output = subprocess.check_output(["wmic", "cpu", "get", "name"])
            return output.decode().split("\n")[1].strip()

        if operatingSystem == "Linux":
            output = subprocess.check_output(["cat", "/proc/cpuinfo"])
            for line in output.decode().split("\n"):
                if "model name" in line:
                    return line.split(":")[1].strip()

        return platform.processor()
    except Exception:
        return platform.processor()


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


def extractPortFromAddress(addressValue):
    cleanAddress = addressValue.strip().strip("[]")
    if ":" not in cleanAddress:
        return None

    port = cleanAddress.rsplit(":", 1)[-1]
    if "%" in port:
        port = port.split("%", 1)[0]

    if port.isdigit():
        return port
    return None


def parseListeningPorts(commandOutput):
    ports = set()

    for line in commandOutput.split("\n"):
        if not line.strip():
            continue
        if line.startswith("Netid") or line.startswith("Proto"):
            continue

        parts = line.split()
        for part in parts:
            port = extractPortFromAddress(part)
            if port:
                ports.add(port)
                break

    return ports


def getActivePorts():
    # Retrieve listening ports and separate them with semicolons.
    ports = set()

    try:
        operatingSystem = platform.system()
        if operatingSystem == "Windows":
            output = subprocess.check_output(["netstat", "-an"]).decode()
            for line in output.split("\n"):
                if "LISTENING" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        port = parts[1].split(":")[-1]
                        if port.isdigit():
                            ports.add(port)

        if operatingSystem == "Linux":
            linuxCommands = [["ss", "-lntu"], ["netstat", "-lntu"]]
            lastError = None
            for command in linuxCommands:
                try:
                    output = subprocess.check_output(command).decode()
                    ports.update(parseListeningPorts(output))
                    if ports:
                        break
                except Exception as error:
                    lastError = error
            if not ports and lastError is not None:
                raise lastError
    except Exception as error:
        print(f"[WARNING] Active port collection failed: {error}")

    return ";".join(sorted(ports, key=int))


def main():
    csvFile = "assets_audit.csv"
    headers = [
        "Computer Name",
        "IP address",
        "MAC address",
        "Processor Model",
        "Operation System",
        "System time",
        "Internet connection speed",
        "Active ports",
    ]

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

    rows = []
    computerFound = False
    fileExists = os.path.isfile(csvFile)

    if fileExists:
        try:
            with open(csvFile, "r", newline="", encoding="utf-8") as csvInput:
                reader = csv.reader(csvInput)
                next(reader, None)

                for row in reader:
                    if not row:
                        continue

                    if row[0] == currentData[0]:
                        computerFound = True

                        # Exclude the system time because it always changes.
                        previousInformation = row[1:5] + row[6:]
                        currentInformation = currentData[1:5] + currentData[6:]

                        if previousInformation != currentInformation:
                            print(
                                f"\n[WARNING] Information for {row[0]} is "
                                "already present in the CSV file but differs "
                                "from the current scan. Data updated."
                            )
                        else:
                            print(
                                f"\n[INFO] Computer {row[0]} already exists "
                                "in the CSV. No configuration changes detected."
                            )

                        rows.append(currentData)
                    else:
                        rows.append(row)
        except Exception as error:
            print(f"Error reading CSV: {error}")
            return

    if not computerFound:
        print(f"\n[INFO] New computer detected. Adding {currentData[0]} to CSV.")
        rows.append(currentData)

    try:
        with open(csvFile, "w", newline="", encoding="utf-8") as csvOutput:
            writer = csv.writer(csvOutput)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"Audit complete. Data safely written to {csvFile}")
    except Exception as error:
        print(f"Error writing to CSV: {error}")


if __name__ == "__main__":
    main()
