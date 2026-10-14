import contextlib
import csv
import importlib.util
import io
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

projectRoot = Path(__file__).resolve().parents[2]
moduleSpec = importlib.util.spec_from_file_location('auditReview', projectRoot / 'src/pycharm_project_at2/at2.py')
auditModule = importlib.util.module_from_spec(moduleSpec)
moduleSpec.loader.exec_module(auditModule)
headers = ['Computer Name', 'IP address', 'MAC address', 'Processor Model', 'Operation System', 'System time', 'Internet connection speed', 'Active ports']
currentRecord = ['PC-TEST', '192.168.1.50', 'AA-BB-CC-DD-EE-FF', 'CPU X', 'Linux 6', '12/11/2026 09:00:00', '25Mb/s', '80;443']
collectorNames = ['getComputerName', 'getIPAddress', 'getMACAddress', 'getProcessor', 'getOS', 'getSystemTime', 'getInternetSpeed', 'getActivePorts']

def runCase(caseName, priorRows, expectedRows, expectedMessage):
    previousDirectory = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as temporaryDirectory:
            os.chdir(temporaryDirectory)
            if priorRows is not None:
                with open('assets_audit.csv', 'w', newline='', encoding='utf-8') as outputFile:
                    csv.writer(outputFile).writerows([headers] + priorRows)
            capturedOutput = io.StringIO()
            with contextlib.ExitStack() as patches:
                for collectorName, value in zip(collectorNames, currentRecord):
                    patches.enter_context(patch.object(auditModule, collectorName, return_value=value))
                patches.enter_context(contextlib.redirect_stdout(capturedOutput))
                auditModule.main()
            with open('assets_audit.csv', newline='', encoding='utf-8') as inputFile:
                resultRows = list(csv.reader(inputFile))
            assert resultRows == [headers] + expectedRows, (caseName, resultRows)
            assert expectedMessage in capturedOutput.getvalue(), capturedOutput.getvalue()
            print('PASS:', caseName)
    finally:
        os.chdir(previousDirectory)

otherRecord = ['PC-OTHER'] + currentRecord[1:]
oldRecord = currentRecord.copy()
oldRecord[5] = '11/11/2026 08:00:00'
changedRecord = oldRecord.copy()
changedRecord[1] = '192.168.1.10'
runCase('Create missing audit file', None, [currentRecord], 'New computer detected')
runCase('Append new computer and retain other record', [otherRecord], [otherRecord, currentRecord], 'New computer detected')
runCase('Timestamp only change does not warn', [oldRecord], [currentRecord], 'No configuration changes detected')
runCase('Changed IP warns and replaces record', [changedRecord], [currentRecord], '[WARNING]')
runCase('Blank row is skipped', [[], otherRecord], [otherRecord, currentRecord], 'New computer detected')
runCase('Duplicate matching rows remain duplicated', [oldRecord, oldRecord], [currentRecord, currentRecord], 'Audit complete')
runCase('Malformed unrelated row is preserved', [['BROKEN']], [['BROKEN'], currentRecord], 'Audit complete')
print('Checks use mocked computer data and temporary CSV files; they are not deployment evidence.')
