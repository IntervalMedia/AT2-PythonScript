# Automated asset audit pseudocode

This pseudocode shows how the asset audit works without relying on Python or any other programming language. The process collects the computer's details, checks them against the saved records, and updates the audit file. It reads the existing records once, so it does not repeat the same search unnecessarily.

## Inputs and outputs

### Inputs

- Computer name.
- IP address.
- MAC address.
- Processor model.
- Operating system and version.
- Current system date and time.
- Internet connection speed or connection status.
- Active listening network ports.
- Existing audit file, if one is available.

### Outputs

- An audit file containing its headings and one current record for each computer.
- A message stating whether the computer is new, unchanged, or changed.
- An error message if the audit file cannot be read or written.
- `Unknown` or another suitable status when optional system information cannot be collected.

## Pseudocode algorithm

```text
ALGORITHM UpdateAssetAudit
    CONSTANT AUDIT_FILE ← "assets_audit.csv"
    CONSTANT HEADINGS ← [
        "Computer Name",
        "IP address",
        "MAC address",
        "Processor Model",
        "Operating System",
        "System Time",
        "Internet Connection Speed",
        "Active Ports"
    ]

    OUTPUT "Collecting system information..."

    currentRecord ← COLLECT_AND_SANITISE_SYSTEM_INFORMATION()
    updatedRecords ← empty list
    computerFound ← FALSE

    IF AUDIT_FILE exists THEN
        TRY
            existingRecords ← READ records from AUDIT_FILE, excluding headings

            FOR EACH existingRecord IN existingRecords DO
                IF existingRecord is empty or invalid THEN
                    CONTINUE to the next existingRecord
                END IF

                IF existingRecord.ComputerName = currentRecord.ComputerName
                    AND computerFound = FALSE THEN
                    computerFound ← TRUE

                    previousConfiguration ← all configuration fields in existingRecord
                        except ComputerName and SystemTime
                    currentConfiguration ← all configuration fields in currentRecord
                        except ComputerName and SystemTime

                    IF previousConfiguration = currentConfiguration THEN
                        OUTPUT "Computer already exists; no configuration changes detected."
                    ELSE
                        OUTPUT "Computer already exists; configuration changed and was updated."
                    END IF

                    APPEND currentRecord TO updatedRecords
                ELSE IF existingRecord.ComputerName = currentRecord.ComputerName THEN
                    OUTPUT "Duplicate computer record ignored."
                ELSE
                    APPEND existingRecord TO updatedRecords
                END IF
            END FOR
        CATCH file read error
            OUTPUT "The audit file could not be read."
            TERMINATE algorithm without changing AUDIT_FILE
        END TRY
    END IF

    IF computerFound = FALSE THEN
        APPEND currentRecord TO updatedRecords
        OUTPUT "New computer detected and added to the audit."
    END IF

    TRY
        WRITE HEADINGS and updatedRecords TO AUDIT_FILE
        OUTPUT "Audit completed successfully."
    CATCH file write error
        OUTPUT "The audit file could not be written."
    END TRY
END ALGORITHM


ALGORITHM CollectAndSanitiseSystemInformation
    computerName ← GET computer name
    ipAddress ← GET primary IP address

    IF primary IP address cannot be obtained THEN
        ipAddress ← GET IP address using local computer name
    END IF

    macAddress ← GET and format MAC address
    IF MAC address cannot be obtained THEN
        macAddress ← "Unknown"
    END IF

    processorModel ← GET processor model using an operating-system-supported method
    IF processor model cannot be obtained THEN
        processorModel ← GET generic processor information
    END IF

    operatingSystem ← GET operating system name and version
    systemTime ← GET current date and time

    TRY
        internetSpeed ← MEASURE a fixed-size download over elapsed time
        IF elapsed time is zero THEN
            internetSpeed ← "Unknown"
        END IF
    CATCH connection or measurement error
        internetSpeed ← "Unknown (Offline)"
    END TRY

    TRY
        activePorts ← GET listening ports supported by the operating system
        REMOVE duplicate ports
        SORT ports numerically
    CATCH port collection error
        activePorts ← any ports collected so far, or an empty value
    END TRY

    currentRecord ← [
        computerName,
        ipAddress,
        macAddress,
        processorModel,
        operatingSystem,
        systemTime,
        internetSpeed,
        activePorts
    ]

    FOR EACH field IN currentRecord DO
        CONVERT field to text
        REPLACE line breaks with spaces
        REMOVE leading and trailing spaces
    END FOR

    RETURN currentRecord
END ALGORITHM
```

## Desk check

The following examples use `PC-01` as the current computer. The system time is not included in the configuration comparison because it changes on every run.

| Test | Audit file | Record found | Configuration match | Write result | Processing | Expected output |
| --- | --- | --- | --- | --- | --- | --- |
| 1. First audit | Does not exist | Not applicable | Not applicable | Success | Add the current `PC-01` record and create the file. | New computer detected. Audit completed successfully. |
| 2. Existing computer, no changes | Exists and can be read | `PC-01` found | True | Success | Replace the saved record with the current record so its system time is updated. | Computer already exists; no configuration changes detected. Audit completed successfully. |
| 3. Existing computer, changed configuration | Exists and can be read | `PC-01` found | False | Success | Replace the old `PC-01` record with the current record. | Computer already exists; configuration changed and was updated. Audit completed successfully. |
| 4. Different computers only | Exists and can be read | No | Not applicable | Success | Keep all valid records and append `PC-01`. | New computer detected. Audit completed successfully. |
| 5. Empty or invalid row | Exists and can be read | No valid match | Not applicable | Success | Skip the invalid row, keep valid records, and append `PC-01`. | New computer detected. Audit completed successfully. |
| 6. Duplicate matching records | Exists and can be read | `PC-01` found more than once | Either | Success | Replace the first match and ignore later duplicates. | Matching status message, duplicate ignored, and audit completed successfully. |
| 7. Read failure | Exists but cannot be read | Unknown | Unknown | Not attempted | Stop without changing the existing file. | The audit file could not be read. |
| 8. Write failure | Missing or read successfully | Depends on records | Depends on match | Failure | Prepare the updated records, but fail while saving them. | The audit file could not be written. |

### Configuration comparison examples

| Current record | Saved record | Values compared | Match result | Action |
| --- | --- | --- | --- | --- |
| `PC-01`, `192.168.1.10`, `AA-BB-CC-DD-EE-FF`, `Intel i5`, `Windows 11`, `10:30`, `50 Mb/s`, `80;443` | Same values with system time `09:00` | IP address, MAC address, processor, operating system, internet speed, and active ports | True | Report no configuration change and update the record time. |
| `PC-01`, `192.168.1.20`, `AA-BB-CC-DD-EE-FF`, `Intel i5`, `Windows 11`, `10:30`, `50 Mb/s`, `80;443` | Same values except IP address `192.168.1.10` | IP address, MAC address, processor, operating system, internet speed, and active ports | False | Report a configuration change and replace the saved record. |
| `PC-01`, current configuration | Saved record belongs to `PC-02` | Computer names are checked first | Not applicable | Keep the `PC-02` record and add `PC-01` after the search ends. |

### System information checks

| Situation | Expected processing | Stored value |
| --- | --- | --- |
| Primary IP lookup succeeds | Use the primary IP address. | Detected IP address. |
| Primary IP lookup fails | Try local computer-name resolution. | Fallback IP address. |
| MAC address lookup fails | Continue the audit. | `Unknown`. |
| Processor-specific lookup fails | Use generic processor information. | Generic processor value. |
| Internet test fails | Continue the audit without a speed result. | `Unknown (Offline)`. |
| Port collection fails | Keep any ports already collected, or use an empty value. | Partial list or empty value. |

### Amendment made after desk checking

The original read-error branch displayed an error but then continued. This could replace an unreadable audit file with a new file containing only the current computer. The algorithm now terminates after a read failure and leaves the existing file unchanged. 
No other changes were needed because the remaining test cases produce a defined result and finish normally.

## How the algorithm works

The algorithm starts by collecting the details needed for one audit record. It cleans each value before saving it by converting it to text, removing extra spaces, and replacing line breaks. If a value cannot be collected, the algorithm tries a fallback method. If that also fails, it records `Unknown` instead of stopping the whole audit.

If the audit file already exists, the algorithm checks each saved record once. It skips empty or invalid rows. Records for other computers are copied into the updated list. When the computer name matches, the old record is replaced with the new one. Any extra records with the same computer name are ignored so that the file keeps only one current record for that computer.

The computer name is used to find the matching record, so it is not part of the configuration comparison. The system time is also left out because it changes every time the audit runs. The remaining fields are compared to decide whether the computer's configuration has changed.

If there is no audit file or no matching computer, the current computer is added as a new record. If an existing file cannot be read, the algorithm stops without changing it. This avoids losing records that may still be recoverable. The algorithm then writes the headings and records to the audit file. If writing fails, it displays an error message so the user knows the audit was not saved.

The algorithm always terminates because each loop has a fixed amount of data to process. It checks the saved records, the fields in one record, and the active ports, then stops. Checking the audit file in a single pass also avoids unnecessary searches. As the file grows, the work increases in direct proportion to the number of saved records.
