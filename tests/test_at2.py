import ast
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pycharm_project_at2 import at2


class AT2Tests(unittest.TestCase):
    def testSanitizeRemovesLineBreaksAndWhitespace(self):
        self.assertEqual(at2.sanitize("  first\nsecond\r  "), "first second")

    def testSanitizePreventsSpreadsheetFormulaInjection(self):
        self.assertEqual(at2.sanitize("=SUM(A1:A2)"), "'=SUM(A1:A2)")
        self.assertEqual(at2.sanitize("+cmd"), "'+cmd")
        self.assertEqual(at2.sanitize("-1"), "'-1")
        self.assertEqual(at2.sanitize("@value"), "'@value")

    @patch("at2.uuid.getnode", return_value=0xAABBCCDDEEFF)
    def testGetMACAddressUsesExpectedFormat(self, mockGetNode):
        self.assertEqual(at2.getMACAddress(), "AA-BB-CC-DD-EE-FF")
        mockGetNode.assert_called_once_with()

    @patch("at2.urllib.request.urlopen")
    @patch("at2.time.time", side_effect=[100.0, 101.0])
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

    @patch("at2.subprocess.check_output", side_effect=RuntimeError("netstat error"))
    @patch("at2.platform.system", return_value="Linux")
    def testGetActivePortsReportsCollectionFailure(self, mockSystem, mockCheckOutput):
        capturedOutput = io.StringIO()
        with contextlib.redirect_stdout(capturedOutput):
            result = at2.getActivePorts()

        self.assertEqual(result, "")
        self.assertIn("Active port collection failed", capturedOutput.getvalue())

    @patch("at2.getActivePorts", return_value="80;443")
    @patch("at2.getInternetSpeed", return_value="25Mb/s")
    @patch("at2.getSystemTime", return_value="01/01/2026 09:00:00")
    @patch("at2.getOS", return_value="Linux 6")
    @patch("at2.getProcessor", return_value="CPU X")
    @patch("at2.getMACAddress", return_value="AA-BB-CC-DD-EE-FF")
    @patch("at2.getIPAddress", return_value="192.168.1.50")
    @patch("at2.getComputerName", return_value="PC-TEST")
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
        sourceCode = Path("at2.py").read_text(encoding="utf-8")
        syntaxTree = ast.parse(sourceCode)
        functionNames = [
            node.name
            for node in ast.walk(syntaxTree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        invalidNames = [name for name in functionNames if "_" in name]

        self.assertEqual(invalidNames, [])


if __name__ == "__main__":
    unittest.main()
