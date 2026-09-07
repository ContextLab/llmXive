import pytest
from feature_extraction.syntax_validator import validate_snippet_syntax

def test_validate_syntax_valid_python():
    """Test validation of valid Python code."""
    code = "def hello():\n    print('Hello')\n"
    result = validate_snippet_syntax(code)
    
    assert result is True

def test_validate_syntax_invalid_python():
    """Test validation of invalid Python code."""
    code = "def hello(:\n    print('Hello')\n"  # Missing closing paren
    result = validate_snippet_syntax(code)
    
    assert result is False

def test_validate_syntax_empty():
    """Test validation of empty code."""
    code = ""
    result = validate_snippet_syntax(code)
    
    assert result is True  # Empty is technically valid

def test_validate_syntax_comment_only():
    """Test validation of comment-only code."""
    code = "# This is a comment\n"
    result = validate_snippet_syntax(code)
    
    assert result is True