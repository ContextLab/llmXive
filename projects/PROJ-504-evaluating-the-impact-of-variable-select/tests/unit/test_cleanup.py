"""
Unit tests for the code cleanup and refactoring utility.

These tests verify that the cleanup module correctly:
1. Identifies Python files
2. Detects syntax errors
3. Identifies missing docstrings
4. Detects and removes debug code
5. Validates API surface
"""

import ast
import os
import tempfile
from pathlib import Path
from typing import List

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from cleanup import (
    get_python_files,
    check_syntax,
    check_docstrings,
    remove_debug_code,
    DEBUG_PATTERNS
)


class TestGetPythonFiles:
    """Tests for get_python_files function."""

    def test_finds_python_files(self, tmp_path):
        """Test that it correctly finds Python files."""
        # Create a test directory structure
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "test1.py").write_text("print('hello')")
        (code_dir / "test2.py").write_text("def foo(): pass")
        (code_dir / "subdir").mkdir()
        (code_dir / "subdir" / "test3.py").write_text("x = 1")
        
        # Also create non-Python files that should be ignored
        (code_dir / "readme.txt").write_text("not python")
        (code_dir / "__pycache__").mkdir()
        (code_dir / "__pycache__" / "test.py").write_text("ignored")
        
        result = get_python_files(tmp_path)
        
        assert len(result) == 3
        assert all(f.suffix == ".py" for f in result)
        assert not any("__pycache__" in str(f) for f in result)

    def test_returns_empty_list_when_no_code_dir(self, tmp_path):
        """Test that it returns empty list when code directory doesn't exist."""
        result = get_python_files(tmp_path)
        assert result == []

    def test_handles_empty_code_dir(self, tmp_path):
        """Test that it returns empty list for empty code directory."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        result = get_python_files(tmp_path)
        assert result == []

class TestCheckSyntax:
    """Tests for check_syntax function."""

    def test_valid_syntax(self, tmp_path):
        """Test that valid Python syntax returns True."""
        file_path = tmp_path / "valid.py"
        file_path.write_text("def foo():\n    return 42\n")
        
        is_valid, error_msg = check_syntax(file_path)
        
        assert is_valid is True
        assert error_msg == ""

    def test_invalid_syntax(self, tmp_path):
        """Test that invalid Python syntax returns False with error message."""
        file_path = tmp_path / "invalid.py"
        file_path.write_text("def foo(\n    return 42\n")  # Missing closing paren
        
        is_valid, error_msg = check_syntax(file_path)
        
        assert is_valid is False
        assert "Syntax error" in error_msg

    def test_missing_file(self, tmp_path):
        """Test behavior when file doesn't exist."""
        file_path = tmp_path / "nonexistent.py"
        
        is_valid, error_msg = check_syntax(file_path)
        
        assert is_valid is False
        assert "Error reading file" in error_msg

class TestCheckDocstrings:
    """Tests for check_docstrings function."""

    def test_missing_docstring_function(self, tmp_path):
        """Test detection of missing function docstring."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
def foo():
    pass

def bar():
    '''Has docstring'''
    pass
""")
        
        issues = check_docstrings(file_path)
        
        assert len(issues) == 1
        assert issues[0]["name"] == "foo"
        assert issues[0]["kind"] == "function"

    def test_missing_docstring_class(self, tmp_path):
        """Test detection of missing class docstring."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
class Foo:
    pass

class Bar:
    '''Has docstring'''
    pass
""")
        
        issues = check_docstrings(file_path)
        
        assert len(issues) == 1
        assert issues[0]["name"] == "Foo"
        assert issues[0]["kind"] == "class"

    def test_all_have_docstrings(self, tmp_path):
        """Test when all functions/classes have docstrings."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
def foo():
    '''Docstring for foo'''
    pass

class Bar:
    '''Docstring for Bar'''
    pass
""")
        
        issues = check_docstrings(file_path)
        assert len(issues) == 0

    def test_empty_file(self, tmp_path):
        """Test with empty file."""
        file_path = tmp_path / "test.py"
        file_path.write_text("")
        
        issues = check_docstrings(file_path)
        assert issues == []

class TestRemoveDebugCode:
    """Tests for remove_debug_code function."""

    def test_detects_print_statements(self, tmp_path):
        """Test detection of print statements."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
x = 1
print("debug")
y = 2
""")
        
        lines_removed, removed_lines = remove_debug_code(file_path, dry_run=True)
        
        assert lines_removed == 1
        assert 'print("debug")' in removed_lines[0]

    def test_detects_todo_comments(self, tmp_path):
        """Test detection of TODO comments."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
x = 1
# TODO: fix this
y = 2
""")
        
        lines_removed, removed_lines = remove_debug_code(file_path, dry_run=True)
        
        assert lines_removed == 1
        assert "TODO" in removed_lines[0]

    def test_detects_pdb_set_trace(self, tmp_path):
        """Test detection of pdb.set_trace()."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
x = 1
import pdb
pdb.set_trace()
y = 2
""")
        
        lines_removed, removed_lines = remove_debug_code(file_path, dry_run=True)
        
        assert lines_removed == 2  # Both import pdb and pdb.set_trace()

    def test_removes_debug_code_when_fix(self, tmp_path):
        """Test actual removal of debug code."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
x = 1
print("debug")
y = 2
""")
        
        lines_removed, _ = remove_debug_code(file_path, dry_run=False)
        
        assert lines_removed == 1
        
        # Verify file was modified
        content = file_path.read_text()
        assert 'print("debug")' not in content
        assert "x = 1" in content
        assert "y = 2" in content

    def test_no_debug_code(self, tmp_path):
        """Test file with no debug code."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
def foo():
    '''Docstring'''
    return 42
""")
        
        lines_removed, removed_lines = remove_debug_code(file_path, dry_run=True)
        
        assert lines_removed == 0
        assert removed_lines == []

    def test_multiple_debug_lines(self, tmp_path):
        """Test file with multiple debug lines."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
print("debug1")
x = 1
# TODO: fix
y = 2
# FIXME: later
""")
        
        lines_removed, removed_lines = remove_debug_code(file_path, dry_run=True)
        
        assert lines_removed == 3
        assert len(removed_lines) == 3

class TestDebugPatterns:
    """Tests for debug pattern detection."""

    @pytest.mark.parametrize("pattern_str", [
        "print('test')",
        "print(123)",
        "# TODO: implement",
        "# FIXME: bug",
        "DEBUG: some message",
        "pdb.set_trace()",
        "breakpoint()",
        "import pdb",
        "ipdb.set_trace()",
    ])
    def test_patterns_match_debug_code(self, pattern_str, tmp_path):
        """Test that debug patterns correctly match debug code."""
        file_path = tmp_path / "test.py"
        file_path.write_text(pattern_str)
        
        for pattern in DEBUG_PATTERNS:
            if pattern.search(pattern_str):
                lines_removed, removed_lines = remove_debug_code(file_path, dry_run=True)
                assert lines_removed >= 1
                break
        else:
            # If no pattern matched, the test should fail
            pytest.fail(f"No debug pattern matched: {pattern_str}")

    @pytest.mark.parametrize("normal_code", [
        "x = 1",
        "def foo(): pass",
        "class Bar: pass",
        "import os",
        "# regular comment",
    ])
    def test_patterns_dont_match_normal_code(self, normal_code, tmp_path):
        """Test that debug patterns don't match normal code."""
        file_path = tmp_path / "test.py"
        file_path.write_text(normal_code)
        
        lines_removed, _ = remove_debug_code(file_path, dry_run=True)
        assert lines_removed == 0