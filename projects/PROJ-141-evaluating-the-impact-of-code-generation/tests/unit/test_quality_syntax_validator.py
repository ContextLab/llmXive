"""
Unit tests for code/quality/syntax_validator.py
Tests for syntax error detection and handling.
"""
import unittest
import sys
from pathlib import Path

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from quality.syntax_validator import (
    validate_syntax,
    create_error_response
)


class TestSyntaxValidator(unittest.TestCase):
    """Unit tests for syntax validation functionality."""

    def test_validate_syntax_valid(self):
        """Test validation of valid Python code."""
        code = """
def hello():
    print("Hello, World!")
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_syntax_missing_colon(self):
        """Test validation of code with missing colon."""
        code = """
def hello()
    print("Hello")
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIn("SyntaxError", error_msg)

    def test_validate_syntax_unclosed_paren(self):
        """Test validation of code with unclosed parenthesis."""
        code = """
def hello():
    print("Hello"
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)

    def test_validate_syntax_invalid_indent(self):
        """Test validation of code with invalid indentation."""
        code = """
def hello():
print("Hello")
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)

    def test_validate_syntax_empty_code(self):
        """Test validation of empty code."""
        code = ""
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_syntax_comment_only(self):
        """Test validation of comment-only code."""
        code = "# This is a comment"
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_syntax_complex_valid(self):
        """Test validation of complex valid code."""
        code = """
class Calculator:
    def __init__(self):
  self.value = 0
    
    def add(self, x):
  self.value += x
  return self.value
    
    def multiply(self, x):
  self.value *= x
  return self.value

calc = Calculator()
result = calc.add(5).multiply(2)
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_syntax_lambda(self):
        """Test validation of lambda expressions."""
        code = """
f = lambda x: x * 2
result = f(5)
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_syntax_decorator(self):
        """Test validation of decorators."""
        code = """
def decorator(func):
    def wrapper(*args, **kwargs):
  return func(*args, **kwargs)
    return wrapper

@decorator
def hello():
    return "Hello"
"""
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_create_error_response(self):
        """Test error response creation."""
        error_msg = "SyntaxError: invalid syntax"
        submission_id = "test-sub-123"
        line_number = 5
        
        response = create_error_response(error_msg, submission_id, line_number)
        
        self.assertEqual(response['submission_id'], submission_id)
        self.assertEqual(response['error'], error_msg)
        self.assertEqual(response['line_number'], line_number)
        self.assertIn('timestamp', response)

    def test_create_error_response_no_line(self):
        """Test error response without line number."""
        response = create_error_response("Generic error", "test-456")
        self.assertIsNone(response.get('line_number'))

    def test_validate_syntax_return_format(self):
        """Test that validate_syntax returns correct format."""
        code = "def foo(): pass"
        result = validate_syntax(code)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsNone(result[1]) or isinstance(result[1], str)

    def test_validate_syntax_large_code(self):
        """Test validation of large code blocks."""
        code = "\n".join([f"line_{i} = {i}" for i in range(1000)])
        is_valid, error_msg = validate_syntax(code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)


if __name__ == '__main__':
    unittest.main()