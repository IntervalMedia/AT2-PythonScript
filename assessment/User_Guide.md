# Midtown IT Asset Audit User Guide

**Project:** ICTPRG434 ICTPRG435 AT2  
**Date:** 19 November 2026

The asset audit records one computer's details in `assets_audit.csv` each time it runs. Use the same CSV sequentially on each authorised computer to build a shared audit. It does not collect every network computer remotely.

## Requirements

Use an authorised Windows or Linux computer with Python installed and permission to read system details and write the audit folder. The project currently specifies Python 3.14 or later. No extra Python audit libraries are required for direct execution. An IDE is optional when running the script.

The script uses operating-system commands for processor and port information. Check that the required commands are available. Internet access is used only for the approximate speed test; failure is recorded as an unavailable result. Target-platform testing is still required before relying on the script operationally.

## Files

| File | Purpose |
| --- | --- |
| `src/pycharm_project_at2/at2.py` | Collects information and updates the CSV |
| `src/pycharm_project_at2/main.py` | Launches the same audit using a neighbouring at2.py |
| `src/pycharm_project_at2/assets_audit.csv` | Existing audit file stored beside the scripts |
| `tests/` | Automated tests, run from the project root |
| `assessment/Testing_Report.md` | Automated results and pending practical evidence |

## Before running

Back up the existing CSV, close it in Excel and make sure only one operator is updating it. Use an approved storage device or folder and restrict access because the file contains computer and network details. Confirm the operating system's correct date and time.

The program writes to the current working directory. Running from the project root creates or updates a different CSV from the one already stored in the source folder. To use the existing source-folder audit, first change into `src/pycharm_project_at2` and run the script there. When moving between computers, carry `at2.py` and the same backed-up CSV together. Keep `main.py` too if using the launcher.

## Run the audit

On Windows, open a terminal in the folder containing `at2.py` and the intended CSV:

```text
py -3.14 at2.py
```

On Linux, from that same audit folder:

```text
python3 at2.py
```

Check `python3 --version` first on Linux. Use the approved interpreter and record its actual version. The same folder can launch the audit through `python3 main.py` on Linux or `py -3.14 main.py` on Windows. Use the direct-file commands documented here; the installed package entry point has not been verified.

Wait for collection to finish, read any warnings and confirm the completion message. Open the CSV afterwards and check that it contains eight columns and the expected computer record. The file is a plain CSV readable by Excel, rather than an Excel workbook.

## Understand the output

| Message or value | Meaning and action |
| --- | --- |
| New computer detected | No matching computer name was found; the current record is added |
| No configuration changes detected | Compared values match; the current timestamp is still saved |
| Information differs from the current scan | The record is replaced and a warning is shown; review the changed details |
| Error reading CSV | The script preserves the original. Check the listed header, row or encoding error on a copy. |
| Error writing to CSV | The update could not be saved. Check permissions, disk space or whether Excel still has the file open. |
| Duplicate computer record ignored | The audit keeps the first saved row per other computer and writes the current computer’s new row once. |
| Active port collection failed | The listener list could not be collected. Check command availability and rerun. |
| Unavailable in IP address | Both IPv4 methods failed to find a usable network address. |
| Unknown in Processor Model | The platform-specific command and generic processor lookup gave no usable model. |
| Unknown (Offline) | Both speed services failed; this does not prove the computer itself has no internet connection |
| Apostrophe before a value | The collector value was protected against spreadsheet formula interpretation |

Computer names match regardless of case. Renaming a computer creates a new record. Give each computer a unique name. System time is refreshed on every run and excluded from the configuration comparison. Measured speed remains part of the comparison, so ordinary speed variation may produce a warning.

Active ports are local listening TCP ports on Windows and Linux. The CSV lists unique IPv4 and IPv6 listener port numbers in numeric order, separated by semicolons.

## Gather the three computer evidence

Use three distinct authorised computers or VMs with unique names, including Windows and Linux. Keep the same CSV and run one computer at a time. After each run, record the date, operating system, computer name, interpreter version, console output and saved CSV row. Compare the collected name, IP, MAC and ports with the operating system's own tools.

On Windows, useful checks include `hostname`, `ipconfig /all`, `Get-NetTCPConnection -State Listen` and `Get-CimInstance Win32_Processor`. On Linux, use `hostname`, `ip address`, `cat /proc/cpuinfo` and `ss -lnt`. These commands inspect the local computer.

Repeat one computer without changing comparison fields, then with a controlled change such as a test VM's approved IP adjustment. Keep screenshots of the actual program output. Complete the table in the submission checklist and retain the final shared CSV. Mocked records from automated tests do not count as three real computers.

## Troubleshooting and limits

Use a UTF-8 audit file with the original eight headings in their original order. Each data row needs eight fields and a computer name. The script skips blank lines and stops on invalid input before saving.

Windows collects local TCP listeners through PowerShell and uses `netstat` if that command fails. Linux uses `ss` and falls back to `netstat`. Audit commands have a five-second timeout.

The speed result estimates the rate of a short download. A blocked service or timeout can leave the estimate unavailable.

The script writes the update to a temporary file in the audit folder, closes it, then replaces the existing CSV. If a write or replacement fails, the existing CSV remains available.

## Developer documentation and checks

To view automatically generated help for the audit module from the script folder, run:

```text
python3 -m pydoc at2
```

On Windows, replace `python3` with `py -3.14`. The module's main guard prevents an audit from starting when imported for help. Some audit functions have block comments rather than docstrings, so the source remains the fuller internal reference. The launcher `main()` has a short docstring.

From the project root, run the automated tests:

```text
python3 -m unittest discover -s tests -t . -v
```

Use the Windows interpreter command where applicable. Review the separate testing report for the exact scope of the current tests. PyCharm breakpoints, watches and variable inspection should supplement the automated tests.
