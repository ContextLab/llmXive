"""
Contract tests for code/feature_extractor/ast_parser.py.

These tests verify the AST parsing logic.
They test:
1. Parsing of a valid Python file (should succeed).
2. Parsing of malformed syntax (should raise a syntax error).
"""
import pytest
import tempfile
import os
import ast
from pathlib import Path

# Import the module under test.
# T012 implementation provides these functions.
from code.feature_extractor.ast_parser import parse_file, parse_string


class TestAstParser:
    """Contract tests for AST parser functionality."""

    def test_parse_valid_file(self):
        """
        Contract test: Verify that a valid Python file is parsed successfully.
        Expected: Returns a valid AST object (ast.AST) or a dictionary of features.
        """
        # Create a temporary file with valid Python code
        valid_code = """
        def hello_world():
            x = 1
            if x > 0:
                print("Hello")
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(valid_code)
            temp_path = f.name

        try:
            result = parse_file(temp_path)
            # Contract: Result should not be None
            assert result is not None, "Parser returned None for valid file"
            
            # Depending on implementation, result might be an AST node or a dict
            if isinstance(result, ast.AST):
                # If returning an AST, verify it's valid
                assert result is not None
            elif isinstance(result, dict):
                # If returning features, verify structure
                assert 'cyclomatic_complexity' in result or 'tokens' in result or 'ast' in result
            else:
                # Fallback: just ensure it's not None and is a meaningful object
                assert result is not None
        finally:
            os.unlink(temp_path)

    def test_parse_invalid_syntax(self):
        """
        Contract test: Verify that malformed syntax raises an error or is handled gracefully.
        Expected: Raises SyntaxError or returns None/error indicator.
        """
        invalid_code = """
        def broken(
            x = 1
            # Missing closing parenthesis and colon
        """
        
        # Test parse_string - should raise SyntaxError
        with pytest.raises(SyntaxError):
            parse_string(invalid_code)

        # Test parse_file with invalid content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(invalid_code)
            temp_path = f.name

        try:
            # Depending on implementation, this might raise SyntaxError or return None
            # The contract requires it to NOT return a valid AST for invalid code.
            try:
                result = parse_file(temp_path)
                # If it returns a result, it must be None for invalid syntax
                assert result is None, "Parser should return None for invalid syntax"
            except SyntaxError:
                # Also acceptable: raising SyntaxError
                pass
        finally:
            os.unlink(temp_path)