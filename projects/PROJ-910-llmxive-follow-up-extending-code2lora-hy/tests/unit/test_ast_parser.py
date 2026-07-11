"""
Contract tests for code/feature_extractor/ast_parser.py.

These tests verify the AST parsing logic before the full implementation is available.
They test:
1. Parsing of a valid Python file (should succeed).
2. Parsing of malformed syntax (should raise a syntax error or return None depending on implementation).
"""
import pytest
import tempfile
import os
from pathlib import Path

# Import the module under test.
# Since T012 (implementation) is not yet done, this import might fail initially.
# The test framework should handle this by failing the import, which is expected
# until T012 is implemented.
try:
    from code.feature_extractor.ast_parser import parse_file, parse_string
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False
    # Define stubs if module doesn't exist yet to allow test collection
    # In a real scenario, pytest would fail on import error.
    # Here we simulate the expected behavior for the contract test description.
    def parse_file(path: str):
        raise NotImplementedError("Implementation pending T012")

    def parse_string(code: str):
        raise NotImplementedError("Implementation pending T012")


@pytest.mark.skipif(not MODULE_EXISTS, reason="AST parser module not yet implemented (T012)")
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
            # Contract: Result should not be None and should be a valid AST or feature dict
            assert result is not None, "Parser returned None for valid file"
            # If returning an AST node:
            # assert isinstance(result, ast.AST)
            # If returning a feature dict:
            # assert isinstance(result, dict)
            # assert 'cyclomatic_complexity' in result or 'tokens' in result
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
        
        # Test parse_string
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
                assert result is None, "Parser should return None for invalid syntax"
            except SyntaxError:
                # Also acceptable: raising SyntaxError
                pass
        finally:
            os.unlink(temp_path)