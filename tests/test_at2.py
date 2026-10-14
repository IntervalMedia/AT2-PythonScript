import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import at2


class AT2Tests(unittest.TestCase):
    def testSanitizeRemovesLineBreaksAndWhitespace(self):
        self.assertEqual(at2.sanitize("  first\nsecond\r  "), "first second")

    @patch("at2.uuid.getnode", return_value=0xAABBCCDDEEFF)
    def testGetMACAddressUsesExpectedFormat(self, mockGetNode):
        self.assertEqual(at2.getMACAddress(), "AA-BB-CC-DD-EE-FF")
        mockGetNode.assert_called_once_with()

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
