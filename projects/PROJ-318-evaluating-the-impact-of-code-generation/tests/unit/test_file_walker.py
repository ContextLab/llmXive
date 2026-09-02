"""
Unit tests for the file walker utility.

These tests verify that walk_python_files, collect_python_files,
and count_python_files correctly identify Python files and handle
exclusions as expected.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from code.utils.file_walker import (
    walk_python_files,
    collect_python_files,
    count_python_files,
    FileWalkerException
)


class TestFileWalker:
    """Test suite for file walker utilities."""

    @pytest.fixture
    def temp_repo_structure(self):
        """Create a temporary directory structure mimicking a Python repo."""
        root = tempfile.mkdtemp(prefix="test_file_walker_")
        
        # Create directory structure
        dirs = [
            "src",
            "src/utils",
            "tests",
            "tests/unit",
            ".git",
            ".git/objects",
            "venv",
            "docs",
            "__pycache__"
        ]
        for d in dirs:
            os.makedirs(os.path.join(root, d), exist_ok=True)
        
        # Create Python files
        py_files = [
            "src/main.py",
            "src/utils/helper.py",
            "tests/test_main.py",
            "tests/unit/test_helper.py",
            "docs/conf.py",
            "setup.py",
            "README.md",  # Not a Python file
            ".git/config",  # Not a Python file
            "venv/bin/activate",  # Not a Python file
            "__pycache__/module.cpython-39.pyc"  # Not a Python file
        ]
        
        for f in py_files:
            full_path = os.path.join(root, f)
            with open(full_path, 'w') as fh:
                fh.write("# Test file\n")
        
        yield root
        
        # Cleanup
        shutil.rmtree(root)

    def test_walk_python_files_basic(self, temp_repo_structure):
        """Test basic walking and yielding of Python files."""
        files = list(walk_python_files(temp_repo_structure))
        
        # Should find all .py files except those in excluded dirs
        # Excluded: .git, venv, __pycache__
        expected_count = 5  # src/main.py, src/utils/helper.py, tests/test_main.py, tests/unit/test_helper.py, docs/conf.py, setup.py
        assert len(files) == expected_count
        
        # Verify all are .py files
        for f in files:
            assert f.suffix == '.py'
            assert f.exists()

    def test_walk_python_files_generator_behavior(self, temp_repo_structure):
        """Test that walk_python_files returns a generator."""
        result = walk_python_files(temp_repo_structure)
        # Check if it's a generator
        import types
        assert isinstance(result, types.GeneratorType)

    def test_walk_python_files_excludes_git(self, temp_repo_structure):
        """Test that .git directory is excluded."""
        files = list(walk_python_files(temp_repo_structure))
        
        for f in files:
            assert '.git' not in str(f)

    def test_walk_python_files_excludes_venv(self, temp_repo_structure):
        """Test that venv directory is excluded."""
        files = list(walk_python_files(temp_repo_structure))
        
        for f in files:
            assert 'venv' not in str(f)

    def test_walk_python_files_excludes_pycache(self, temp_repo_structure):
        """Test that __pycache__ directory is excluded."""
        files = list(walk_python_files(temp_repo_structure))
        
        for f in files:
            assert '__pycache__' not in str(f)

    def test_walk_python_files_custom_exclude_dirs(self, temp_repo_structure):
        """Test custom directory exclusions."""
        files = list(walk_python_files(
            temp_repo_structure,
            exclude_dirs={'docs', '__pycache__', '.git', 'venv'}
        ))
        
        for f in files:
            assert 'docs' not in str(f)

    def test_walk_python_files_custom_exclude_patterns(self, temp_repo_structure):
        """Test custom filename pattern exclusions."""
        files = list(walk_python_files(
            temp_repo_structure,
            exclude_patterns={'test_*.py'}
        ))
        
        for f in files:
            assert 'test_' not in f.name

    def test_walk_python_files_nonexistent_dir(self):
        """Test exception when directory does not exist."""
        with pytest.raises(FileWalkerException) as exc_info:
            list(walk_python_files("/nonexistent/path/12345"))
        
        assert "does not exist" in str(exc_info.value)

    def test_walk_python_files_is_file(self, temp_repo_structure):
        """Test exception when path is a file, not a directory."""
        # Find an existing file
        py_file = os.path.join(temp_repo_structure, "src/main.py")
        
        with pytest.raises(FileWalkerException) as exc_info:
            list(walk_python_files(py_file))
        
        assert "not a directory" in str(exc_info.value)

    def test_collect_python_files(self, temp_repo_structure):
        """Test collect_python_files returns a list."""
        files = collect_python_files(temp_repo_structure)
        
        assert isinstance(files, list)
        assert len(files) > 0
        
        for f in files:
            assert isinstance(f, Path)
            assert f.suffix == '.py'

    def test_collect_python_files_returns_same_as_walk(self, temp_repo_structure):
        """Test that collect_python_files returns same results as walk_python_files."""
        walk_files = list(walk_python_files(temp_repo_structure))
        collect_files = collect_python_files(temp_repo_structure)
        
        assert len(walk_files) == len(collect_files)
        
        # Compare paths
        walk_paths = sorted([str(f) for f in walk_files])
        collect_paths = sorted([str(f) for f in collect_files])
        
        assert walk_paths == collect_paths

    def test_count_python_files(self, temp_repo_structure):
        """Test count_python_files returns correct count."""
        count = count_python_files(temp_repo_structure)
        
        # Should match the number of .py files found
        expected_count = 5  # src/main.py, src/utils/helper.py, tests/test_main.py, tests/unit/test_helper.py, docs/conf.py, setup.py
        assert count == expected_count

    def test_count_python_files_empty_dir(self):
        """Test counting in an empty directory."""
        empty_dir = tempfile.mkdtemp(prefix="test_empty_")
        try:
            count = count_python_files(empty_dir)
            assert count == 0
        finally:
            shutil.rmtree(empty_dir)

    def test_walk_python_files_no_py_files(self):
        """Test walking a directory with no Python files."""
        no_py_dir = tempfile.mkdtemp(prefix="test_no_py_")
        try:
            # Create a non-Python file
            with open(os.path.join(no_py_dir, "readme.txt"), 'w') as f:
                f.write("No Python here")
            
            files = list(walk_python_files(no_py_dir))
            assert len(files) == 0
        finally:
            shutil.rmtree(no_py_dir)

    def test_walk_python_files_nested_structure(self, temp_repo_structure):
        """Test that deeply nested files are found."""
        # Create a deeply nested structure
        deep_path = os.path.join(temp_repo_structure, "a", "b", "c", "d")
        os.makedirs(deep_path, exist_ok=True)
        
        deep_file = os.path.join(deep_path, "deep.py")
        with open(deep_file, 'w') as f:
            f.write("# Deep file\n")
        
        files = list(walk_python_files(temp_repo_structure))
        
        assert any("deep.py" in str(f) for f in files)

    def test_walk_python_files_permission_error_simulation(self):
        """Test handling of permission errors (simulated via non-existent path)."""
        # This is tested via the nonexistent directory test
        # Real permission errors would require OS-level setup
        pass