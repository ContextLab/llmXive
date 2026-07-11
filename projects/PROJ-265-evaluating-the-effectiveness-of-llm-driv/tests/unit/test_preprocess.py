"""Unit tests for the preprocess module."""
import pytest
import ast
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocess import sanitize_code, preprocess_function, CodeSanitizer


class TestCodeSanitizer:
    """Tests for the CodeSanitizer AST transformer."""

    def test_removes_print_call(self):
        """Test that print() calls are removed."""
        code = "print('hello')"
        sanitized = sanitize_code(code)
        assert 'mock_safe_call' in sanitized
        assert 'print' not in sanitized.split('mock_safe_call')[0]

    def test_removes_open_call(self):
        """Test that open() calls are removed."""
        code = "open('file.txt')"
        sanitized = sanitize_code(code)
        assert 'mock_safe_call' in sanitized

    def test_removes_os_import(self):
        """Test that os import is removed."""
        code = "import os\nos.system('ls')"
        sanitized = sanitize_code(code)
        # os import should be removed or mocked
        assert 'import os' not in sanitized or 'mock_stdlib_placeholder' in sanitized

    def test_mocks_math_import(self):
        """Test that math import is mocked."""
        code = "import math\nmath.sqrt(4)"
        sanitized = sanitize_code(code)
        # Math should be mocked
        assert 'mock_stdlib_placeholder' in sanitized

    def test_preserves_function_definition(self):
        """Test that function definitions are preserved."""
        code = "def add(a, b):\n    return a + b"
        sanitized = sanitize_code(code)
        assert 'def add' in sanitized
        assert 'return a + b' in sanitized

    def test_handles_complex_code(self):
        """Test sanitization of complex code."""
        code = """
        import os
        import math

        def complex_func(x):
            print(x)
            result = math.sqrt(x)
            with open('file.txt') as f:
                pass
            return result
        """
        sanitized = sanitize_code(code)
        assert 'def complex_func' in sanitized
        assert 'mock_safe_call' in sanitized
        assert 'mock_stdlib_placeholder' in sanitized


class TestPreprocessFunction:
    """Tests for the preprocess_function function."""

    def test_successful_preprocessing(self):
        """Test successful preprocessing of valid code."""
        code = "def test():\n    return 42"
        result = preprocess_function(code)
        assert result['success'] is True
        assert result['code'] is not None
        assert 'def test' in result['code']

    def test_invalid_syntax(self):
        """Test preprocessing of invalid syntax."""
        code = "def test(\n    return 42"  # Missing closing paren
        result = preprocess_function(code)
        assert result['success'] is False
        assert result['error'] is not None

    def test_with_io_calls(self):
        """Test preprocessing of code with I/O calls."""
        code = "def test():\n    print('hello')\n    return 42"
        result = preprocess_function(code)
        assert result['success'] is True
        assert 'mock_safe_call' in result['code']

    def test_no_mock_stdlib(self):
        """Test preprocessing without mocking stdlib."""
        code = "import math\nmath.sqrt(4)"
        result = preprocess_function(code, mock_stdlib=False)
        assert result['success'] is True
        # Should not be mocked when mock_stdlib=False
        assert 'mock_stdlib_placeholder' not in result['code']


class TestSanitizeCode:
    """Tests for the sanitize_code function."""

    def test_empty_code(self):
        """Test sanitization of empty code."""
        with pytest.raises(ValueError):
            sanitize_code("")

    def test_whitespace_only(self):
        """Test sanitization of whitespace-only code."""
        with pytest.raises(ValueError):
            sanitize_code("   \n\n  ")

    def test_single_line(self):
        """Test sanitization of single line code."""
        code = "x = 1"
        sanitized = sanitize_code(code)
        assert 'x = 1' in sanitized

    def test_multiline(self):
        """Test sanitization of multiline code."""
        code = "x = 1\ny = 2\nz = x + y"
        sanitized = sanitize_code(code)
        assert 'x = 1' in sanitized
        assert 'y = 2' in sanitized
        assert 'z = x + y' in sanitized

    def test_with_comments(self):
        """Test that comments are preserved."""
        code = "# This is a comment\nx = 1"
        sanitized = sanitize_code(code)
        assert '# This is a comment' in sanitized

    def test_with_docstring(self):
        """Test that docstrings are preserved."""
        code = '"""This is a docstring"""\ndef test(): pass'
        sanitized = sanitize_code(code)
        assert '"""This is a docstring"""' in sanitized