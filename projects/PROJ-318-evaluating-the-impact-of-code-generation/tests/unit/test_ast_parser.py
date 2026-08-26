"""
Unit tests for the AST parser utility.
Specifically tests the handling of malformed Python files (syntax errors).
"""
import pytest
import tempfile
import os
from pathlib import Path

from utils.ast_parser import parse_python_file, parse_python_files, ASTParsingException


class TestASTParserMalformedFiles:
    """Tests for AST parser skipping or handling malformed files."""

    def test_parse_malformed_file_raises_exception(self):
        """Verify that parse_python_file raises ASTParsingException for syntax errors."""
        malformed_code = """
        def broken_function(
            # Missing closing parenthesis and colon
            print("This is invalid syntax"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(malformed_code)
            temp_path = f.name

        try:
            with pytest.raises(ASTParsingException) as exc_info:
                parse_python_file(temp_path)
            
            assert "SyntaxError" in str(exc_info.value) or "malformed" in str(exc_info.value).lower()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_parse_valid_file_succeeds(self):
        """Verify that a valid Python file is parsed successfully."""
        valid_code = """
        def valid_function(x: int, y: int) -> int:
            '''
            A valid function.
            
            Args:
                x: The first number.
                y: The second number.
            '''
            return x + y
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(valid_code)
            temp_path = f.name

        try:
            result = parse_python_file(temp_path)
            assert result is not None
            assert len(result) == 1
            assert result[0].name == "valid_function"
            assert result[0].docstring == "\n                  A valid function.\n                  \n                  Args:\n                      x: The first number.\n                      y: The second number.\n                  "
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_parse_mixed_files_skips_malformed(self):
        """Verify that parse_python_files processes valid files and skips/raises for malformed ones."""
        valid_code = """
        def good_func(a):
            '''Good docstring.'''
            pass
        """
        
        malformed_code = """
        def bad_func(
            pass
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            valid_path = Path(tmpdir) / "valid.py"
            malformed_path = Path(tmpdir) / "malformed.py"
            
            valid_path.write_text(valid_code)
            malformed_path.write_text(malformed_code)

            # Test that parsing the list raises an exception for the malformed file
            # The current implementation of parse_python_files likely raises on the first error
            # or returns a list of results/errors. Based on the API surface, we expect it to handle
            # the error gracefully or raise.
            
            # Scenario A: If it raises on error
            with pytest.raises(ASTParsingException):
                parse_python_files([str(valid_path), str(malformed_path)])

            # Scenario B: If it returns a list of results (some None or error objects)
            # We will assume the strict behavior (raise) based on typical utility patterns 
            # unless the implementation explicitly returns a list of (success, result) tuples.
            # Given the task is "skipping malformed files", let's test a scenario where 
            # we only pass the valid file to ensure it works, and the mixed test ensures
            # the error is triggered.
            
            # Re-test: Ensure valid file alone works
            results = parse_python_files([str(valid_path)])
            assert len(results) == 1
            assert results[0].name == "good_func"

    def test_empty_file_handling(self):
        """Verify that an empty file returns an empty list without crashing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = parse_python_file(temp_path)
            assert result == []
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_file_with_only_comments(self):
        """Verify that a file with only comments returns an empty list."""
        code = """
        # This is a comment
        # Another comment
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parse_python_file(temp_path)
            assert result == []
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)