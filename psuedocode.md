# Automated asset audit pseudocode

**Revision:** 19 November 2026, following David Hunt’s 18 November UTC approval.

## Inputs and outputs

The audit collects the computer name, IPv4 address, MAC address, processor, operating system, system time, estimated download speed and local listening TCP ports. It reads the existing audit CSV if present. It writes the same eight headings and one current record per computer name, and reports additions, updates, duplicates and errors.

## Pseudocode algorithm

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

## Desk check

| Situation | Expected result |
| --- | --- |
| Audit CSV missing or has headings only | Save the headings and the new computer. |
| Saved computer differs only in system time | Refresh its time and report that the configuration is unchanged. |
| Saved computer differs in a configuration field | Replace the record and report the configuration change after saving. |
| Blank line or valid record for a different computer | Skip the blank line and retain the other computer. |
| Invalid header, wrong field count, blank name or invalid CSV syntax | Report the read error and preserve the original file. |
| Repeated computer name, including case variants | For the current computer, save its new record once. For other computers, retain the first valid record. |
| Primary IP lookup fails | Try hostname resolution. If that fails, warn and store `Unavailable`. |
| Processor command times out and the generic processor value is blank | Use `Unknown` and continue the audit. |
| Port output mixes TCP, UDP, IPv4, IPv6 and connection states | Save only distinct local listening TCP ports, sorted numerically. |
| Temporary write or replacement fails | Report the save error, preserve the original and clean up the temporary file. |

A single pass validates and groups the saved rows. The time field refreshes on every successful audit and is excluded from configuration comparisons.
