# Automated Processes Portfolio of Evidence

**Units:** ICTPRG434 Automate processes and ICTPRG435 Write scripts for software applications  
**Assessment:** AT2 Automated Processes Algorithmic and Scripting Solution Portfolio  
**Prepared:** 12 November 2026  
**Student name:** [Enter full name]  
**Student number:** [Enter student number]  
**Assessor:** [Enter assessor name]  
**Due date and submission date:** [Enter dates]

This portfolio maps the Midtown IT asset audit to the assessment tasks. David Hunt’s change approval is recorded below. PyCharm debugging, three-computer deployment evidence and final signoff remain pending. Retain the supplied assessment cover, instructions and declaration when transferring these responses into the original Word portfolio. The student completes the declaration personally.

## Part 1 Specifying software application requirements and formulating automated solutions

### 1.1 Application requirements

**a Process to automate.** The program automates the collection and recording of computer configuration details for Midtown IT's asset audit. An operator runs the same Python script sequentially on each authorised Windows or Linux computer, carrying the shared audit file between computers where necessary.

**b Expected outcomes.** The audit CSV contains the computer name, IPv4 address, MAC address, processor model, operating system, system time, estimated internet speed and local listening TCP ports. A new computer is added and a matching computer is updated, with a warning when its compared configuration differs.

**c Functionality and security.** The script validates the header and data rows, sanitises new and retained values, keeps one record per computer name and atomically replaces the audit after a complete write. It reports invalid input and failed saves while preserving the existing file.

**d Operating environment.** The target environment is an authorised Windows or Linux computer with Python, a writable folder or USB drive and standard operating-system networking commands. Internet access is needed for the download estimate. The project uses PyCharm and only Python standard-library modules. Its project metadata specifies Python 3.14 or later; the review tests ran on Python 3.14.6 on macOS. macOS results do not establish Windows or Linux compatibility. The supplied assessment does not specify Python 3.11.

### 1.2 Requirements documented using the report structure

Part 1 of `Algorithmic_Solution_Report.md` follows the supplied report's headings and documents the process, expected functionality, security and environment. Transfer this content into the supplied Word template to satisfy the required template format. Template formatting remains pending.

### 1.3 Requirements confirmation

The initial requirements and tools draft remains in Appendix A. The actual CSV review proposal and David Hunt’s reply are recorded in the communication log.

### 1.4 Responses and requirement updates

David Hunt approved the CSV changes and required the five edge cases in the same release. He specified local listening TCP ports for both platforms. The communication log records his conditions for final signoff.

### 1.5 Potential solutions and selection

**a Potential solutions.** The options are manual spreadsheet entry, a portable Python script using CSV, and a central web or database application. Manual entry is slow and prone to typing errors. A central application adds hosting and dependencies. A portable standard-library script best matches the supplied sequential audit process.

**b Discussion.** Jonathan Coates sent the review findings and proposed corrections on 18 November 2026. David Hunt’s reply approved the changes and clarified which edge cases were required.

**c Selection process.** I compared the options against the required eight fields, Windows and Linux support, portability, security, installation effort and maintenance. Python with CSV meets the brief with the least extra infrastructure. The report contains the comparison table and reasons.

**d Confirmation.** The approval applies to the requested implementation changes. Final acceptance requires practical results and a separate signoff.

## Part 2 Developing algorithmic solution

### 2.1 Pseudocode

Part 2 and `psuedocode.md` define the inputs, outputs, validation, collector fallbacks, comparison and atomic save. The pseudocode was revised before the corresponding code changes.

### 2.2 Algorithm logic

Sequence collects and cleans the eight values before processing the file. Selection checks whether a file exists, whether a record matches and whether the compared fields changed. Iteration reads each saved record once, preserving unrelated records and replacing the current computer's record. The system time is excluded from comparison because it changes on every run. The comparison still includes measured speed, so normal speed variation can produce a warning. A single pass is O(n) for n saved rows and avoids repeated searches. Port sorting is O(p log p) for p distinct ports.

### 2.3 Review and desk check

The report desk checks missing files, unchanged and changed computers, blank lines, duplicate names, malformed rows, and read and save failures. The automated suite verifies these behaviours and the required collector edge cases.

### 2.4 Algorithm amendments

The revised algorithm validates all saved rows, stops on malformed data, deduplicates computer names and preserves the existing file on error. It covers IP and processor fallback, command timeouts, local listening TCP ports and atomic replacement.

## Part 3 Determining integrated development environment and scripting language

### 3.1 Python characteristics framework protocols and object model

Python is a high-level scripting language with readable, indentation-based syntax, dynamic typing and exceptions. It supports procedural and object-oriented programming. For this command-line project, the standard library provides the required CSV, networking, operating-system, timing and testing functions. A web framework would add dependencies without helping the required portable workflow.

Every Python value is an object with an identity, type and value. Variables refer to objects. Lists and sets are mutable; strings and tuples are immutable. The script uses the iteration protocol in loops, the sequence protocol for list slicing and the context-manager protocol to close files, sockets and HTTP responses. These are language protocols; the network operations separately use IPv4 sockets and HTTPS downloads.

PyCharm is the selected IDE because the project already has PyCharm configuration and benefits from breakpoints, stepping, variable inspection and integrated tests. The existing configuration names Python 3.14. An email requesting manager confirmation is included in the report; confirmation remains pending.

### 3.2 Translation into Python

The implementation is `src/pycharm_project_at2/at2.py`. It separates collection, sanitisation, port parsing and CSV updating into functions. `main.py` calls the audit script. The code uses camelCase function and variable names, four-space indentation and block comments, matching the local coding standards in the reviewed excerpts. PyCharm project files show an IDE configuration but do not prove a debugging session took place.

### 3.3 Efficient syntax and item manipulation

**a Basic language elements.** `csvFile` is a Path, `AUDIT_HEADINGS` and `currentData` are ordered lists, and `seenNames` and `ports` are sets. The list order determines CSV columns. Sets track computer names and distinct ports. Conditions and the CSV loop validate and merge saved records in a single pass.

**b Item manipulation.** The current script uses:

```python
previousInformation = row[1:5] + row[6:]
currentInformation = currentData[1:5] + currentData[6:]
```

Slicing selects the fields to compare and concatenation joins them into new lists. Index 0 is the computer name already used for matching. Index 5 is the changing timestamp. Comparing two lists is shorter and clearer than a separate condition for each field, and slicing leaves the source records unchanged.

### 3.4 Debugging testing omissions and errors

All 34 automated tests passed on macOS with Python 3.14.6. Standard-library trace measured 95.8% line coverage in the audit module. See `Testing_Report.md` for the tested cases and practical evidence still to collect.

The tests do not prove execution on Windows or Linux, real internet-speed accuracy, operation on three computers or use of PyCharm's debugger. IDE evidence must show an actual paused breakpoint, variables and stepping through the relevant branch. No such session is claimed by this portfolio.

### 3.5 Internal documentation

The code includes full-sentence block comments explaining the IP fallback, MAC formatting, timestamp formatting, speed measurement, port collection, formula protection and exclusion of system time from comparison. Existing `evidence/block-comments.txt.png` is a rendered code excerpt, not proof of an IDE debugging session. `User_Guide.md` documents both the audit module and launcher.

### 3.6 Code amendments

The code now implements the approved CSV protections and all five collector and save edge cases. The testing report records their automated results.

### 3.7 Discussion of omissions and errors

The communication log records the email proposal and David Hunt’s approval. It also records the revised implementation and the evidence still needed for final signoff.

## Part 4 Finalising scripts and obtaining signoff

### 4.1 User and internal documentation

`User_Guide.md` covers prerequisites, working-directory selection, running both Python files, interpreting output, collecting three-computer evidence, troubleshooting and safe CSV handling. Internal comments remain in `at2.py`, and the launcher has an entry-point docstring. The guide includes commands for displaying function documentation and running automated tests.

### 4.2 Final documentation package

| Required item | Project evidence |
| --- | --- |
| Pseudocode and desk check | Report Part 2 and the revised `psuedocode.md` |
| Python implementation | `src/pycharm_project_at2/at2.py` and `main.py` |
| Internal documentation | Comments and docstrings in the scripts |
| Test report | `Testing_Report.md` and current captured test output |
| User documentation | `User_Guide.md` |
| Requirements and contingency responses | Report Parts 1 and 5 |
| Approval and practical evidence | Change approval in the communication log. Practical evidence and final signoff are pending. |

### 4.3 Presentation and signoff

David approved the corrections. Presentation of the final package and signoff are pending practical evidence. Signature and approval fields are for the actual participants.

**Project manager signature:** ____________________  **Date:** __________  
**Software developer signature:** ____________________  **Date:** __________  
**Approval:** [ ] Granted  [ ] Not granted  
**Feedback:** __________________________________________________________

### 4.4 Requested changes and resubmission

The approved changes have been implemented and retested. Resubmission and final acceptance remain pending.

### 4.5 Run on at least three computers

The supplied CSV contains one record for `Jm1.local` running Darwin. It does not satisfy the requirement for three computers or establish Windows and Linux support. Run the script on three distinct authorised physical or virtual computers, including Windows and Linux, using one shared CSV. Keep console captures and the final CSV. Repeat one computer unchanged and after a controlled configuration change to demonstrate update behaviour. Do not substitute mocked test records for these runs.

## Part 5 Contingency tasks

### 5.1 Minor client changes after coding

I would record the requested changes, their purpose and deadline, then assess their effect on the requirements, code, security and testing. I would obtain the required manager approval and preserve the working version in version control. I would make the changes separately, update the pseudocode and documentation, and run targeted tests plus the existing regression tests. Finally, I would show the revised result to the manager, record acceptance and release the approved version with a rollback copy available.

### 5.2 Newer IDE version becomes available

I would confirm the requested IDE version and check its release notes and organisational requirements. I would back up the project and trial the new IDE separately, retaining the same Python interpreter and run settings initially. I would run the tests, debug the CSV branches and compare output with the existing baseline. An IDE upgrade does not automatically require a Python upgrade; I would assess an interpreter change separately if requested. After resolving any issues, I would update setup instructions, seek approval and keep the previous working setup available for rollback.

## Communication log

| Date | Topic | Discussion or prepared action | Stakeholder | Communication type and status |
| --- | --- | --- | --- | --- |
| 12 November 2026 | Requirements and solution | Draft confirmation request in report Appendix A | Manager acting as assessor | Draft email; not sent |
| 12 November 2026 | Python and PyCharm | Justification and confirmation request prepared | Manager acting as assessor | Draft email; not sent |
| 12 November 2026 | Review gaps | Test findings and practical evidence requirements prepared | Manager acting as assessor | Draft review message; no discussion recorded |
| 18 November 2026, 15:56 AEST | CSV review and change proposal | Jonathan reported test findings and requested approval for CSV validation, duplicate handling, temporary-file saves and decisions on five edge cases. | Jonathan Coates to David Hunt | Email sent |
| 18 November 2026, 22:55 UTC (19 November, 08:55 AEST) | Change approval | David approved revising pseudocode first, then implementing validation, duplicate handling and temporary-file saves. He required IP fallback, command timeouts, processor fallback, consistent listening TCP ports and replacement after a complete write in this version. He requested automated results and practical Windows/Linux evidence before final signoff. | David Hunt to Jonathan Coates | Approval received in [AT2 email thread](https://mail.google.com/mail/u/0/#all/1a1e98de9a63dd61) |
| 19 November 2026 | Implementation and testing | Revised the pseudocode before changing the script. All 34 automated tests passed. The three-computer run, resulting shared CSV, PyCharm capture and final signoff remain pending. | Project record | Local update |
| To be recorded | Final approval | Present code, report, tests and practical evidence | Manager and developer | Pending presentation and signoff |
