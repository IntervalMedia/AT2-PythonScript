# Automated Processes Algorithmic Solution Report

**Organisation:** Midtown IT  
**Author:** [Enter full student name]  
**Student number:** [Enter student number]  
**Project reference:** ICTPRG434 ICTPRG435 AT2  
**Date:** 12 November 2026

This report describes the Midtown IT asset audit and records David Hunt’s approved CSV and collector changes. The automated tests are complete. The three-computer Windows/Linux run and final signoff remain pending.

## PART 1 Specifying software application requirements and formulating automated solution

Midtown IT needs current computer information to support its risk assessment and Incident Response Plan. Automating collection reduces repeated manual entry and keeps the same information together in one file.

### Automated process description

An operator runs the audit script on each authorised computer in sequence. The script collects its details, reads the shared CSV, checks for the computer name and either adds or updates the record. When compared information changes, it displays a warning. It collects information from the local computer; it does not remotely scan every computer from one workstation.

### Client automation expectations

The client expects one portable audit process for Windows and Linux, a single CSV suitable for Excel, and clear messages about new computers, configuration changes and failures. The script must remain relevant to the audit and use Python without installing additional third-party audit tools.

#### Expected functionality of automated processes

| Field | Required output and current approach |
| --- | --- |
| Computer Name | Local host name from `platform.node()`; used to match records |
| IP address | Primary IPv4 address chosen through a UDP socket, with hostname-resolution fallback |
| MAC address | `uuid.getnode()` formatted as six uppercase hexadecimal pairs separated by hyphens |
| Processor Model | Windows WMI command, Linux CPU information or generic platform fallback |
| Operating system | System name and release |
| System time | Local date and time in day/month/year and 24-hour time |
| Internet connection speed | Approximate download rate in integer megabits per second, or an unavailable status |
| Active ports | Numerically sorted unique port numbers separated by semicolons |

The CSV is created when absent. A saved computer is matched by name regardless of case. The audit keeps the first record for each other computer and saves one current row for this computer. It excludes the name and system time from configuration comparisons and includes the measured speed. Windows and Linux both collect sorted, unique local listening TCP ports.

#### Security requirements

Audit only authorised computers and protect the resulting configuration information through restricted access and approved storage. The current script converts collected values to strings, removes line breaks and surrounding whitespace, and prefixes values beginning with `=`, `+`, `-` or `@` to reduce spreadsheet formula execution. Its subprocess calls use argument lists rather than shell interpolation. HTTPS is used for download estimates, and a read error stops processing before writing.

The script validates the headings and each row before saving. It sanitises both new and retained values and writes the updated data to a temporary file in the same folder. The audit replaces the original only after the write, flush, sync and close succeed.

### Required operating environment

The operational targets are Windows and Linux computers with Python, a writable audit folder and permission to read local configuration. Windows uses WMIC for the processor and the Windows listener API through PowerShell for ports, with a netstat fallback. Linux uses CPU information from the operating system and ss or netstat for ports. Failed primary and hostname IP lookups produce a warning and an Unavailable value.

PyCharm provides development, testing and debugging. The project configuration selects Python 3.14 and `pyproject.toml` requires version 3.14 or later. The review environment used Python 3.14.6 on macOS. The supplied brief names Python without requiring version 3.11. Windows and Linux execution remains to be demonstrated. The source imports only standard-library modules; installing the package through its build configuration is separate from running the portable script directly.

### Confirming application requirements

Appendix A records Jonathan’s actual review proposal and David Hunt’s reply. An earlier requirements and tools draft is retained for reference.

### Document potential solutions

| Option | Fit to the brief | Main limitation |
| --- | --- | --- |
| Manual spreadsheet collection | Uses an existing spreadsheet process | Repeated manual work and transcription errors |
| Portable Python standard-library script with CSV | Matches sequential execution, required language and shared file | Needs Python and platform-specific collection checks |
| Central web application or database service | Could centralise future audit collection | Adds hosting, deployment and maintenance beyond this brief |

I recommend the portable script because it meets the required workflow with limited setup. It reads the file once, preserves other records, compares the current computer and saves the updated audit. The recommendation assumes computers have unique host names and operators use the same audit file sequentially.

### Potential solution discussion with the manager or team members

David approved the CSV changes and directed that Active ports contain local listening TCP ports on both platforms. Appendix A records the required edge cases and evidence for final signoff.

### Confirm best solution with the manager

David Hunt approved the proposed CSV protections and required the five edge cases in his reply of 18 November 2026 UTC. The audit keeps the portable Python and CSV approach.

## PART 2 Developing algorithmic solution

The pseudocode was revised before changing the Python implementation. It validates and merges records in a single pass.

### Pseudocode algorithm

**Inputs** Local host name, IPv4 address, MAC address, processor model, operating system, system time, internet-speed estimate, local listening TCP ports and any existing CSV.
**Outputs** Updated CSV, record-status messages, collection warnings and file errors.

```text
ALGORITHM UpdateAssetAudit
    AUDIT_FILE ← "assets_audit.csv"
    HEADINGS ← ["Computer Name", "IP address", "MAC address", "Processor Model",
                "Operation System", "System time", "Internet connection speed", "Active ports"]

    OUTPUT "Collecting system information..."
    currentRecord ← COLLECT and SANITISE the eight system values
    IF currentRecord has a blank computer name THEN
        REPORT that the current record is invalid and STOP
    END IF

    updatedRecords ← empty list
    seenNames ← empty set
    currentName ← case-insensitive key of currentRecord.ComputerName

    TRY to open AUDIT_FILE
        IF AUDIT_FILE is missing THEN
            CONTINUE with an empty audit
        ELSE
            READ using strict CSV syntax and UTF-8 with an optional initial byte order mark
            REQUIRE the first row to match HEADINGS exactly
            FOR EACH row after the headings DO
                IF row is a blank line THEN
                    CONTINUE to the next row
                END IF
                REQUIRE exactly eight fields and a nonblank computer name
                SANITISE every field, including fields in saved records
                savedName ← case-insensitive key of row.ComputerName

                IF savedName is in seenNames THEN
                    WARN that the duplicate was ignored
                ELSE
                    ADD savedName to seenNames
                    IF savedName = currentName THEN
                        COMPARE the six configuration fields, excluding name and system time
                        QUEUE a change warning or unchanged message as appropriate
                        APPEND currentRecord to updatedRecords
                    ELSE
                        APPEND row to updatedRecords
                    END IF
                END IF
            END FOR
        END IF
    ON read, decoding, CSV syntax or validation error
        REPORT the error and STOP before saving
    END TRY

    IF currentName is absent from seenNames THEN
        APPEND currentRecord to updatedRecords
        QUEUE a new-computer message
    END IF

    TRY
        CREATE a uniquely named temporary file in the AUDIT_FILE directory
        WRITE HEADINGS and updatedRecords to the temporary file
        FLUSH, sync to disk and close the temporary file
        ATOMICALLY REPLACE AUDIT_FILE with the completed temporary file
            (Python operation: os.replace)
    ON save or replacement error
        REPORT the error and STOP
    ALWAYS
        REMOVE any remaining temporary file from this attempt
    END TRY

    OUTPUT the queued record status and report success
END ALGORITHM


ALGORITHM CollectAndSanitiseSystemInformation
    computerName ← GET local computer name
    ipAddress ← GET the primary IPv4 address from the route selected by a UDP socket
    TREAT loopback and unspecified addresses as unavailable
    IF primary lookup fails THEN
        ipAddress ← RESOLVE the local computer name to IPv4
        IF hostname lookup also fails THEN
            WARN that the IP address could not be determined
            ipAddress ← "Unavailable"
        END IF
    END IF

    macAddress ← GET and format MAC address, or "Unknown" on failure
    processorModel ← GET the first nonblank processor model from the OS command
    IF the command is missing, fails, times out or gives no usable model THEN
        processorModel ← GET generic processor information using the platform library
        ON systems where the generic lookup starts a command, run it in a timed Python process
    END IF
    IF the generic lookup fails or gives no usable model THEN
        processorModel ← "Unknown"
    END IF

    operatingSystem ← GET operating system name and version
    systemTime ← GET current date and time
    internetSpeed ← ESTIMATE download speed using the configured HTTPS tests
    USE "Unknown" for zero elapsed time or "Unknown (Offline)" if both tests fail

    RUN every external command with a five-second timeout
    TREAT a command timeout as a failed command and follow its fallback

    IF Windows THEN
        GET numeric local TCP listener ports from the Windows networking API via PowerShell
        IF that command fails THEN
            READ numeric netstat output and select TCP rows with a listening state
        END IF
    ELSE IF Linux THEN
        READ numeric listening TCP rows from ss
        IF ss fails THEN
            USE numeric netstat output and select TCP or TCP6 rows in LISTEN state
        END IF
    END IF
    EXTRACT the port from the local endpoint only (IPv4 or IPv6)
    DEDUPLICATE valid ports, SORT numerically and JOIN with semicolons
    IF supported port commands all fail THEN
        WARN and use an empty ports field
    END IF

    FOR EACH collected field DO
        CONVERT to text, remove carriage returns, replace line feeds with spaces,
            and trim surrounding whitespace
        PREFIX an apostrophe to values starting with "=", "+", "-" or "@"
    END FOR
    RETURN the eight fields in heading order
END ALGORITHM
```

The implementation follows the revised design. Automated coverage for the approved changes is recorded in `Testing_Report.md`.

### Explain the algorithm logic

Sequence puts data collection and sanitisation before validation, comparison and saving. Selection handles missing and invalid files, duplicates and record changes. Iteration checks each saved row once. A set of names prevents duplicate records.

The comparison excludes the matched name and changing system time. Retained records stay in their original order. The CSV pass takes O(n) time and keeps O(n) rows. Sorting takes O(p log p) for p distinct ports. Each subprocess started by the audit has a five-second timeout.

### Testing the algorithm – Desk Check Table

For these traces, the current computer is `PC-TEST`, the current IP is `192.168.1.50`, and all other comparison fields are fixed unless stated. These are desk checks, not claims of three-computer deployment.

| Input state | Processing and variable change | Intended output | Current script comparison |
| --- | --- | --- | --- |
| No file | Append current row when the name is absent | Create headings and one record | Confirmed by temporary-file check |
| File has only PC-OTHER | Preserve the other row and append the current row | Two computer records | Confirmed |
| PC-TEST differs only in time | Match the saved name and compare equal configuration | Update time without warning | Confirmed |
| PC-TEST has old IP .10 | Match the saved name and detect the changed IP | Warning and replacement with .50 | Confirmed |
| Blank row before valid record | Skip blank; process next row | Valid records retained | Confirmed |
| Two PC-TEST records | Replace the first match and skip later duplicates | One current PC-TEST record | Verified with disposable CSV |
| One-field unrelated row | Detect wrong width; stop before write | Preserve original and report invalid data | Verified with disposable CSV |
| Invalid text encoding | Read fails; stop | Original bytes unchanged | Existing automated test passes |
| Failed save | Temporary save fails; preserve original | Report write error | Verified with simulated save failures |
| Both IP lookups fail | Use Unavailable and warn | Continue collecting other fields | Verified with mocked IP lookups |

The desk check covers the normal update flow and the file-preservation branches. See the testing report for observed automated results.

## PART 3 Determining integrated development environment IDE and scripting language

### Selecting Python framework and IDE

Python's clear syntax, dynamic typing, exceptions and standard library suit a small audit script. Variables refer to objects, which have a type, identity and value. Mutable lists hold ordered CSV fields and mutable sets deduplicate ports; immutable strings hold collected text. Loops use Python's iteration protocol, slicing uses the sequence protocol and `with` blocks use the context-manager protocol for resource cleanup.

I recommend Python's standard library without an additional application framework. The solution needs local collection and a CSV rather than a web application. PyCharm supplies project navigation, syntax checking, breakpoints, watches, stepping and an integrated test runner. Alternatives include VS Code with Python extensions and IDLE with fewer project tools. Existing project files already select PyCharm and Python 3.14. The manager confirmation request is in Appendix A.

### Translating pseudocode into scripts

The implementation is `src/pycharm_project_at2/at2.py`. Collection functions supply the individual fields. `sanitize()` cleans collected and retained values. `main()` coordinates validation, merging and safe saving. The launcher is `main.py`. The project uses camelCase function names, four-space indentation and full-sentence comments.

#### Select the most efficient syntax elements and controls available in the selected scripting language

Lists keep the required field order and work directly with `csv.writer`. The script selects between platform-specific collection methods with `if`, reads saved records with `for row in reader`, and skips blank rows using `continue`. A set removes duplicate port numbers before numeric sorting. These structures are sufficient for a sequential CSV audit and avoid extra dependencies.

Basic data excerpt from `main()`:

```python
csvFile = Path("assets_audit.csv")
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
```

The earlier source and test images in `evidence/` are historical. See the current test transcript in Appendix B’s companion testing report. Capture final code and a paused debugger during the pending PyCharm session.

#### Use the debugging features of the selected IDE to debug and test the scripts

All 34 automated tests passed on macOS with Python 3.14.6. Standard-library trace measured 95.8% line coverage in the audit module. The tests used mock collector values and disposable local CSV files. See `Testing_Report.md` for the per-requirement results.

A practical IDE session still needs to pause at `main()`, the matching branch and an error handler, inspect the working values and step through each branch. Capture the PyCharm Variables panel and test runner. This has not been evidenced by the existing rendered source images. Windows and Linux collection and three-computer execution also remain unverified.

#### Create internal documentation comments according to organisational guidelines

Docstrings and block comments describe the IP and processor fallbacks, TCP listener collection, comparison and save steps. Appendix A records the completed email consultation about the identified defects.

#### Identify Item Manipulation

```python
row[1:5] + row[6:] == currentData[1:5] + currentData[6:]
```

The slices select all configuration fields except the matching name and timestamp. Concatenation creates new lists for one equality comparison without modifying either original row. This is concise and avoids repeated field-by-field conditions.

## PART 4 Finalising scripts and obtaining sign-off

The documentation package includes the portfolio, testing report, user guide, submission checklist, revised pseudocode and Python scripts.

The user guide explains working-directory selection, CSV validation and update messages. The remaining practical tasks are a PyCharm debugging capture and the three-computer Windows/Linux run with its resulting shared CSV.

### Python Code SIGN-OFF

Final code signoff remains pending. David’s email approved the scope of the changes.

**Project manager signature:** ____________________  **Date:** __________  
**Software developer signature:** ____________________  **Date:** __________

### Python code NOT APPROVED

Manager feedback and required changes: ___________________________________

### APPROVAL

[ ] Granted  [ ] Not granted

If changes are requested, record the request, amend the affected artefacts, rerun the relevant tests and resubmit. The original supplied portfolio also requires execution on at least three computers. The existing single Darwin record does not meet that requirement.

## PART 5 Contingency tasks

### Introduction

Unexpected requests must be recorded, assessed and tested so they do not silently alter the agreed audit or damage working records.

### Contingency task 1

If the client requests minor changes after coding, I would document the request, purpose and deadline. I would compare it with the agreed requirements and assess its impact on security, output, effort and testing. After approval, I would preserve the working version and make the changes in a separate version-control branch. I would update the algorithm, tests and instructions, run targeted and regression tests, then present the result for acceptance. I would record signoff before releasing the revised version and retain a rollback copy.

### Contingency task 2

If the client requests a newer IDE, I would confirm the version and review its release notes, security and compatibility. I would back up the project and test the new IDE separately with the existing Python interpreter. I would check run configurations, file paths, debugging and test output against the baseline. The IDE is a development tool; it is not required to run the portable script. A request for a new IDE does not itself require a new interpreter. Any requested interpreter upgrade would receive its own compatibility checks. I would update the setup guide, obtain approval and retain the previous working configuration for rollback.

## Appendix A Communication log

| Date | Topic | Discussion or prepared action | Stakeholder | Communication Type |
| --- | --- | --- | --- | --- |
| 12 November 2026 | Requirements | Draft below requests confirmation; no response recorded | Manager acting as assessor | Unsent draft email |
| 12 November 2026 | Solution and IDE | Portable standard-library Python, CSV and PyCharm recommended | Manager acting as assessor | Unsent draft email |
| 12 November 2026 | Omissions and errors | Review message below prepared for discussion | Manager acting as assessor | Unsent draft email |
| 18 November 2026, 15:56 AEST | CSV review and change proposal | Jonathan reported test findings and requested approval for CSV validation, duplicate handling, temporary-file saves and decisions on five edge cases. | Jonathan Coates to David Hunt | Email sent |
| 18 November 2026, 22:55 UTC (19 November, 08:55 AEST) | Change approval | David approved revising pseudocode first, then implementing validation, duplicate handling and temporary-file saves. He required IP fallback, command timeouts, processor fallback, consistent listening TCP ports and replacement after a complete write in this version. He requested automated results and practical Windows/Linux evidence before final signoff. | David Hunt to Jonathan Coates | Approval received in [AT2 email thread](https://mail.google.com/mail/u/0/#all/1a1e98de9a63dd61) |
| 19 November 2026 | Implementation and testing | Revised the pseudocode before changing the script. All 34 automated tests passed. The three-computer run, resulting shared CSV, PyCharm capture and final signoff remain pending. | Project record | Local update |
| To be recorded | Final signoff | Present final files and practical evidence | Manager and developer | Pending |

### Requirements solution and IDE confirmation draft

**To:** [Assessor acting as Midtown IT manager]  
**Subject:** Confirmation of asset audit requirements and tools

Hello,

I propose a portable Python script that runs sequentially on each authorised Windows and Linux computer and maintains one shared CSV. It will record computer name, IP address, MAC address, processor model, operating system, system time, internet connection speed and active ports. It will add new computers, update matching records and warn when compared information changes.

I recommend Python's standard library and PyCharm. This meets the required workflow without extra audit tools or a hosted service. The project currently uses Python 3.14. Please confirm that this version and the proposed tools are acceptable.

Please also confirm whether host names are unique, whether active ports must include TCP and UDP on both systems, and whether normal speed variation should trigger a change warning. I propose excluding the timestamp from comparisons and protecting the original CSV when validation or saving fails.

Please reply with approval or any required changes so I can record the agreed requirements and solution.

Regards,  
[Student name]

### Earlier review draft retained for reference

**To:** [Assessor acting as Midtown IT manager]  
**Subject:** Asset audit testing findings and remaining evidence

Hello,

The current script passes nine automated tests. Additional temporary-file checks confirmed adding, retaining and updating computer records. They also showed that duplicate matching rows remain duplicated and malformed unrelated rows are accepted. The revised algorithm proposes validation, duplicate handling and saving through a temporary file. These changes are not yet implemented.

Other points for review are failed fallback IP resolution, missing command timeouts, unavailable processor commands, inconsistent TCP and UDP collection and protection against interrupted writes. The current speed measurement is an estimate, and failed downloads do not prove the computer is offline.

I still need practical PyCharm debugger evidence and runs on at least three computers, including Windows and Linux. Please confirm the priority of the outstanding fixes and any other changes required before signoff.

Regards,  
[Student name]

### Final presentation draft

**Subject:** Asset audit project for review and signoff

Hello,

Please review the attached portfolio, algorithmic solution report, Python scripts, test report, user guide and practical evidence. Please record approval or the changes required in the signoff section. Outstanding items are listed in the submission checklist and must be resolved before the package is presented as complete.

Regards,  
[Student name]
