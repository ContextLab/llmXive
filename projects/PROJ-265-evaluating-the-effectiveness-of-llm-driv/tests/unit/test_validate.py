"""
Unit tests for code/data/validate.py.

These tests verify that the validation pipeline correctly excludes functions
that raise SyntaxError and properly validates external import counts.
"""

import ast
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

# Import the functions to test from the actual module
from data.validate import (
    check_syntax,
    mock_stdlib_imports,
    count_external_imports,
    validate_function,
)


class TestCheckSyntax(TestCase):
    """Tests for the check_syntax function."""

    def test_valid_python_code(self):
        """Valid Python code should return True and no error."""
        valid_code = """
        def add(a, b):
            return a + b
        """
        is_valid, error_msg = check_syntax(valid_code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_syntax_error_missing_colon(self):
        """Code with a syntax error (missing colon) should return False."""
        invalid_code = """
        def add(a, b)
            return a + b
        """
        is_valid, error_msg = check_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIn("SyntaxError", error_msg)

    def test_syntax_error_invalid_indentation(self):
        """Code with invalid indentation should return False."""
        invalid_code = """
        def add(a, b):
        return a + b
        """
        is_valid, error_msg = check_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIn("IndentationError", error_msg)

    def test_empty_code(self):
        """Empty code should be considered valid (no syntax error)."""
        is_valid, error_msg = check_syntax("")
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_comment_only_code(self):
        """Comment-only code should be valid."""
        code = "# This is a comment\n# Another comment"
        is_valid, error_msg = check_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_unclosed_parenthesis(self):
        """Unclosed parenthesis should raise a syntax error."""
        invalid_code = "def foo(x:\n    pass"
        is_valid, error_msg = check_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)


class TestMockStdlibImports(TestCase):
    """Tests for the mock_stdlib_imports function."""

    def test_mock_stdlib_imports_basic(self):
        """Should replace standard library imports with mock imports."""
        code = """
        import os
        import sys
        import json
        from collections import defaultdict
        """
        mocked = mock_stdlib_imports(code)
        # Should replace 'import os' with 'import mock_os as os'
        self.assertIn("import mock_os as os", mocked)
        self.assertIn("import mock_sys as sys", mocked)
        self.assertIn("import mock_json as json", mocked)

    def test_mock_stdlib_from_import(self):
        """Should handle 'from X import Y' statements."""
        code = """
        from os.path import join
        from sys import argv
        """
        mocked = mock_stdlib_imports(code)
        # from X import Y should become from mock_X import Y
        self.assertIn("from mock_os.path import join", mocked)
        self.assertIn("from mock_sys import argv", mocked)

    def test_no_stdlib_imports(self):
        """Code without stdlib imports should remain unchanged."""
        code = """
        import my_custom_module
        from my_package import something
        """
        mocked = mock_stdlib_imports(code)
        self.assertEqual(mocked, code)

    def test_mixed_imports(self):
        """Should handle a mix of stdlib and custom imports."""
        code = """
        import os
        import my_custom_lib
        from sys import path
        from my_package import utils
        """
        mocked = mock_stdlib_imports(code)
        self.assertIn("import mock_os as os", mocked)
        self.assertIn("import my_custom_lib", mocked)
        self.assertIn("from mock_sys import path", mocked)
        self.assertIn("from my_package import utils", mocked)


class TestCountExternalImports(TestCase):
    """Tests for the count_external_imports function."""

    def test_no_imports(self):
        """Code with no imports should return 0."""
        code = """
        def foo():
            pass
        """
        count = count_external_imports(code)
        self.assertEqual(count, 0)

    def test_only_stdlib_imports(self):
        """Code with only stdlib imports should return 0."""
        code = """
        import os
        import sys
        from json import loads
        """
        count = count_external_imports(code)
        self.assertEqual(count, 0)

    def test_external_imports(self):
        """Code with external imports should count them."""
        code = """
        import pandas as pd
        import numpy
        from sklearn.model_selection import train_test_split
        """
        count = count_external_imports(code)
        # Should count 3 external imports
        self.assertEqual(count, 3)

    def test_mixed_imports_count(self):
        """Should count only external imports, not stdlib."""
        code = """
        import os
        import pandas as pd
        import sys
        import requests
        """
        count = count_external_imports(code)
        # Should count 2 external imports (pandas, requests)
        self.assertEqual(count, 2)

    def test_from_external_import(self):
        """Should count 'from X import Y' for external modules."""
        code = """
        from tensorflow.keras import layers
        from torch import nn
        """
        count = count_external_imports(code)
        self.assertEqual(count, 2)


class TestValidateFunction(TestCase):
    """Tests for the validate_function function."""

    def test_valid_function_with_no_imports(self):
        """A valid function with no imports should pass validation."""
        code = """
        def add(a, b):
            return a + b
        """
        result = validate_function(code, source_id="test_1")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["source_id"], "test_1")
        self.assertIsNone(result["error"])
        self.assertEqual(result["external_import_count"], 0)

    def test_function_with_syntax_error(self):
        """A function with a syntax error should be marked invalid."""
        code = """
        def add(a, b)
            return a + b
        """
        result = validate_function(code, source_id="test_2")
        self.assertFalse(result["is_valid"])
        self.assertIsNotNone(result["error"])
        self.assertIn("SyntaxError", result["error"])

    def test_function_with_too_many_external_imports(self):
        """A function with >3 external imports should be marked invalid."""
        code = """
        import pandas
        import numpy
        import sklearn
        import requests
        def complex_func():
            pass
        """
        result = validate_function(code, source_id="test_3")
        self.assertFalse(result["is_valid"])
        self.assertIsNotNone(result["error"])
        self.assertIn("external imports", result["error"])

    def test_function_with_acceptable_imports(self):
        """A function with <=3 external imports should pass (if syntax valid)."""
        code = """
        import pandas
        import numpy
        def simple_func():
            pass
        """
        result = validate_function(code, source_id="test_4")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["external_import_count"], 2)

    def test_function_with_syntax_error_and_imports(self):
        """Syntax errors should be caught regardless of import count."""
        code = """
        import pandas
        def broken(
            pass
        """
        result = validate_function(code, source_id="test_5")
        self.assertFalse(result["is_valid"])
        self.assertIn("SyntaxError", result["error"])

    def test_empty_function(self):
        """An empty function body (pass) should be valid."""
        code = """
        def empty():
            pass
        """
        result = validate_function(code, source_id="test_6")
        self.assertTrue(result["is_valid"])

    def test_function_with_stdlib_imports_only(self):
        """Functions with only stdlib imports should pass import count check."""
        code = """
        import os
        import sys
        from json import loads
        def stdlib_func():
            pass
        """
        result = validate_function(code, source_id="test_7")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["external_import_count"], 0)

    def test_function_with_mixed_imports_under_limit(self):
        """Mixed stdlib and external imports under limit should pass."""
        code = """
        import os
        import pandas
        import sys
        import numpy
        def mixed_func():
            pass
        """
        result = validate_function(code, source_id="test_8")
        # 2 external imports (pandas, numpy), 2 stdlib (os, sys)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["external_import_count"], 2)

    def test_function_with_exactly_3_external_imports(self):
        """A function with exactly 3 external imports should pass."""
        code = """
        import pandas
        import numpy
        import sklearn
        def three_imports():
            pass
        """
        result = validate_function(code, source_id="test_9")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["external_import_count"], 3)

    def test_function_with_4_external_imports(self):
        """A function with 4 external imports should fail."""
        code = """
        import pandas
        import numpy
        import sklearn
        import requests
        def four_imports():
            pass
        """
        result = validate_function(code, source_id="test_10")
        self.assertFalse(result["is_valid"])
        self.assertIn("external imports", result["error"])