"""
Unit tests for the file_walker module.

Tests verify that the generator correctly filters .py files,
excludes specified directories, and handles edge cases.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

import sys
# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.file_walker import walk_python_files, collect_python_files, count_python_files, FileWalkerException


@pytest.fixture
def temp_repo_structure():
    """Create a temporary directory structure mimicking a Python repo."""
    root = tempfile.mkdtemp()
    
    # Create valid Python files
    (Path(root) / "main.py").touch()
    (Path(root) / "utils.py").touch()
    
    # Create subdirectories with Python files
    subdir = Path(root) / "src"
    subdir.mkdir()
    (subdir / "module.py").touch()
    (subdir / "helper.py").touch()
    
    # Create excluded directories
    pycache = Path(root) / "__pycache__"
    pycache.mkdir()
    (pycache / "cache.pyc").touch() # Should be ignored anyway as not .py
    
    git_dir = Path(root) / ".git"
    git_dir.mkdir()
    (git_dir / "config").touch() # Not .py
    
    # Create a file that matches exclusion pattern
    (Path(root) / "test_dummy.py").touch()
    
    return root


def test_walk_python_files_generates_correct_files(temp_repo_structure):
    """Test that walk_python_files yields all .py files."""
    files = list(walk_python_files(temp_repo_structure))
    
    file_names = {f.name for f in files}
    expected = {"main.py", "utils.py", "module.py", "helper.py", "test_dummy.py"}
    
    assert file_names == expected, f"Expected {expected}, got {file_names}"
    
    # Verify order is deterministic (os.walk order)
    assert len(files) == len(expected)


def test_walk_python_files_excludes_pycache(temp_repo_structure):
    """Test that __pycache__ is excluded."""
    files = list(walk_python_files(temp_repo_structure))
    
    # Should not contain any path with __pycache__
    for f in files:
        assert "__pycache__" not in str(f)


def test_walk_python_files_excludes_git(temp_repo_structure):
    """Test that .git is excluded."""
    files = list(walk_python_files(temp_repo_structure))
    
    for f in files:
        assert ".git" not in str(f)


def test_walk_python_files_custom_exclude_pattern(temp_repo_structure):
    """Test custom exclusion patterns."""
    files = list(walk_python_files(
        temp_repo_structure, 
        exclude_patterns={"test_*.py"}
    ))
    
    file_names = {f.name for f in files}
    assert "test_dummy.py" not in file_names
    assert "main.py" in file_names


def test_collect_python_files(temp_repo_structure):
    """Test collect_python_files returns a list."""
    files = collect_python_files(temp_repo_structure)
    
    assert isinstance(files, list)
    assert len(files) > 0
    assert all(isinstance(f, Path) for f in files)


def test_count_python_files(temp_repo_structure):
    """Test count_python_files returns correct integer."""
    count = count_python_files(temp_repo_structure)
    
    # main.py, utils.py, module.py, helper.py, test_dummy.py = 5
    assert count == 5


def test_walk_python_files_non_existent_dir():
    """Test exception raised for non-existent directory."""
    with pytest.raises(FileWalkerException) as exc_info:
        list(walk_python_files("/non/existent/path"))
    
    assert "does not exist" in str(exc_info.value)


def test_walk_python_files_is_file(temp_repo_structure):
    """Test exception raised if root is a file, not a directory."""
    main_py = Path(temp_repo_structure) / "main.py"
    
    with pytest.raises(FileWalkerException) as exc_info:
        list(walk_python_files(str(main_py)))
    
    assert "not a directory" in str(exc_info.value)


def test_walk_python_files_empty_dir():
    """Test walk on empty directory returns empty generator."""
    empty_dir = tempfile.mkdtemp()
    try:
        files = list(walk_python_files(empty_dir))
        assert files == []
    finally:
        shutil.rmtree(empty_dir)
