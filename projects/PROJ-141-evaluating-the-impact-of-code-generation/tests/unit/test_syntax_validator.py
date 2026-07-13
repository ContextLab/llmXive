"""
Unit tests for syntax validation functionality.

Tests the syntax error detection and handling implemented in
code/quality/syntax_validator.py.
"""
import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.quality.syntax_validator import (
    validate_syntax,
    create_error_response
)


class TestSyntaxValidation(unittest.TestCase):
    """Test cases for syntax validation."""

    def test_validate_valid_code(self):
        """Test validation of syntactically valid code."""
        valid_code = 'def hello():\n    return "world"'
        
        is_valid, error_msg, error_details = validate_syntax(valid_code, 'test_id')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertIsNone(error_details)

    def test_validate_missing_colon(self):
        """Test validation of code missing colon."""
        invalid_code = 'def hello(\n    return "world"'
        
        is_valid, error_msg, error_details = validate_syntax(invalid_code, 'test_id')
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIsNotNone(error_details)
        self.assertEqual(error_details['type'], 'SyntaxError')
        self.assertIn('line', error_details)

    def test_validate_missing_indent(self):
        """Test validation of code with missing indentation."""
        invalid_code = 'def hello():\nreturn "world"'
        
        is_valid, error_msg, error_details = validate_syntax(invalid_code, 'test_id')
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIsNotNone(error_details)

    def test_validate_unclosed_parenthesis(self):
        """Test validation of code with unclosed parenthesis."""
        invalid_code = 'def hello(\n    return "world"'
        
        is_valid, error_msg, error_details = validate_syntax(invalid_code, 'test_id')
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIsNotNone(error_details)

    def test_validate_empty_code(self):
        """Test validation of empty code."""
        empty_code = ''
        
        is_valid, error_msg, error_details = validate_syntax(empty_code, 'test_id')
        
        self.assertTrue(is_valid)  # Empty code is syntactically valid
        self.assertIsNone(error_msg)
        self.assertIsNone(error_details)

    def test_validate_complex_valid_code(self):
        """Test validation of complex but valid code."""
        complex_code = '''
def fibonacci(n):
    """Calculate Fibonacci number."""
    if n <= 1:
  return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(result)
'''
        
        is_valid, error_msg, error_details = validate_syntax(complex_code, 'test_id')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertIsNone(error_details)


class TestCreateErrorResponse(unittest.TestCase):
    """Test cases for error response creation."""

    def test_create_error_response_structure(self):
        """Test that error response has correct structure."""
        error_details = {
            'type': 'SyntaxError',
            'message': 'invalid syntax',
            'line': 1,
            'offset': 5
        }
        
        response = create_error_response('sub_123', 'Syntax error', error_details)
        
        self.assertEqual(response['status'], 'error')
        self.assertEqual(response['code'], 400)
        self.assertEqual(response['message'], 'Syntax error')
        self.assertEqual(response['submission_id'], 'sub_123')
        self.assertIn('error_details', response)
        self.assertIn('timestamp', response)

    def test_create_error_response_contains_details(self):
        """Test that error response contains all error details."""
        error_details = {
            'type': 'SyntaxError',
            'message': 'invalid syntax',
            'line': 10,
            'offset': 5,
            'text': 'def foo(:',
            'submission_id': 'sub_456'
        }
        
        response = create_error_response('sub_456', 'Syntax error', error_details)
        
        self.assertEqual(response['error_details']['line'], 10)
        self.assertEqual(response['error_details']['offset'], 5)
        self.assertEqual(response['error_details']['type'], 'SyntaxError')


if __name__ == '__main__':
    unittest.main()