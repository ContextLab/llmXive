import pytest
from pathlib import Path
import tempfile
import os
from code.utils.validators import (
    get_language_from_extension,
    validate_python_syntax,
    validate_java_syntax,
    validate_file_syntax,
    validate_directory
)

def test_get_language_from_extension_py():
    assert get_language_from_extension(Path("test.py")) == 'python'
    assert get_language_from_extension(Path("test.PY")) == 'python'

def test_get_language_from_extension_java():
    assert get_language_from_extension(Path("Test.java")) == 'java'
    assert get_language_from_extension(Path("Test.kt")) == 'java'
    assert get_language_from_extension(Path("Test.groovy")) == 'java'

def test_get_language_from_extension_unknown():
    assert get_language_from_extension(Path("test.txt")) is None
    assert get_language_from_extension(Path("test.xyz")) is None

def test_validate_python_syntax_valid():
    is_valid, error = validate_python_syntax("def foo():\n    pass")
    assert is_valid is True
    assert error is None

def test_validate_python_syntax_invalid():
    is_valid, error = validate_python_syntax("def foo(\n    pass")
    assert is_valid is False
    assert "SyntaxError" in error

def test_validate_file_syntax_valid_py(tmp_path):
    file_path = tmp_path / "valid.py"
    file_path.write_text("x = 1\n")
    is_valid, error = validate_file_syntax(file_path)
    assert is_valid is True
    assert error is None

def test_validate_file_syntax_invalid_py(tmp_path):
    file_path = tmp_path / "invalid.py"
    file_path.write_text("x =\n")
    is_valid, error = validate_file_syntax(file_path)
    assert is_valid is False
    assert "SyntaxError" in error

def test_validate_file_syntax_missing():
    is_valid, error = validate_file_syntax(Path("/nonexistent/file.py"))
    assert is_valid is False
    assert error == "File not found"

def test_validate_directory(tmp_path):
    # Create valid file
    valid_file = tmp_path / "valid.py"
    valid_file.write_text("a = 1\n")
    
    # Create invalid file
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("b =\n")
    
    # Create non-code file
    other_file = tmp_path / "readme.txt"
    other_file.write_text("hello")

    total, valid, invalid = validate_directory(tmp_path)
    
    assert total == 2
    assert valid == 1
    assert invalid == 1