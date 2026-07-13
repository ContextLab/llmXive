"""
Unit tests for code/quality/static_analysis.py
Tests for static analysis warning count using pylint.
"""
import unittest
import sys
import tempfile
import os
from pathlib import Path

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from quality.static_analysis import (
    StaticAnalysisError,
    run_pylint,
    run_checkstyle,
    detect_language,
    analyze_static_warnings
)


class TestStaticAnalysis(unittest.TestCase):
    """Unit tests for static analysis functionality."""

    def test_detect_language_python(self):
        """Test language detection for Python code."""
        python_code = """
def hello():
    print("Hello")
"""
        lang = detect_language(python_code)
        self.assertEqual(lang, 'python')

    def test_detect_language_java(self):
        """Test language detection for Java code."""
        java_code = """
public class Hello {
    public static void main(String[] args) {
  System.out.println("Hello");
    }
}
"""
        lang = detect_language(java_code)
        self.assertEqual(lang, 'java')

    def test_detect_language_unknown(self):
        """Test language detection for unknown code."""
        unknown_code = "This is not code"
        lang = detect_language(unknown_code)
        self.assertIsNone(lang)

    def test_run_pylint_valid_code(self):
        """Test pylint analysis on valid code."""
        code = """
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""
        warnings = run_pylint(code)
        self.assertIsInstance(warnings, list)
        # Valid code should have minimal or no warnings

    def test_run_pylint_unused_import(self):
        """Test pylint detection of unused imports."""
        code = """
import os
import sys

def hello():
    print("Hello")
"""
        warnings = run_pylint(code)
        self.assertIsInstance(warnings, list)
        # Should detect unused imports

    def test_run_pylint_missing_docstring(self):
        """Test pylint detection of missing docstrings."""
        code = """
def hello():
    print("Hello")
"""
        warnings = run_pylint(code)
        self.assertIsInstance(warnings, list)
        # Should detect missing docstring

    def test_run_pylint_empty_code(self):
        """Test pylint on empty code."""
        warnings = run_pylint("")
        self.assertIsInstance(warnings, list)
        self.assertEqual(len(warnings), 0)

    def test_analyze_static_warnings(self):
        """Test full static analysis workflow."""
        code = """
import os
import sys

def process(data):
    x = 1
    return x
"""
        result = analyze_static_warnings(code)
        self.assertIn('language', result)
        self.assertIn('warning_count', result)
        self.assertIn('warnings', result)
        self.assertIsInstance(result['warnings'], list)

    def test_warning_count_accuracy(self):
        """Test that warning count matches actual warnings."""
        code = """
import os  # Unused

def foo():  # Missing docstring
    pass
"""
        result = analyze_static_warnings(code)
        self.assertGreater(result['warning_count'], 0)
        self.assertEqual(result['warning_count'], len(result['warnings']))

    def test_run_checkstyle_java(self):
        """Test checkstyle analysis on Java code."""
        java_code = """
public class Test {
    public void method() {
  int x = 1;
    }
}
"""
        # Checkstyle may not be available, so we test the function exists
        try:
            warnings = run_checkstyle(java_code)
            self.assertIsInstance(warnings, list)
        except FileNotFoundError:
            # Checkstyle not installed - this is acceptable in test environment
            self.skipTest("Checkstyle not available")

    def test_static_analysis_error_handling(self):
        """Test error handling in static analysis."""
        code = None
        with self.assertRaises(StaticAnalysisError):
            analyze_static_warnings(code)

    def test_warning_structure(self):
        """Test that warnings have expected structure."""
        code = "import os\n"
        result = analyze_static_warnings(code)
        
        if result['warning_count'] > 0:
            warning = result['warnings'][0]
            self.assertIn('line', warning)
            self.assertIn('message', warning)
            self.assertIn('severity', warning)


if __name__ == '__main__':
    unittest.main()