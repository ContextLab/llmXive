"""
Unit tests for the file walker utility.

Tests verify that walk_python_files correctly identifies .py files,
excludes specified directories and patterns, and handles edge cases.
"""

import os
import tempfile
import pytest
from pathlib import Path
from utils.file_walker import walk_python_files, collect_python_files, count_python_files, FileWalkerException


class TestFileWalker:
    """Test cases for file walker functionality."""

    @pytest.fixture
    def temp_project_structure(self):
        """Create a temporary directory structure with Python files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create directory structure
            (root / 'src').mkdir()
            (root / 'src' / 'subdir').mkdir()
            (root / 'tests').mkdir()
            (root / '__pycache__').mkdir()
            (root / '.git').mkdir()
            (root / 'venv').mkdir()
            (root / 'data').mkdir()
            
            # Create Python files
            (root / 'main.py').touch()
            (root / 'src' / 'module.py').touch()
            (root / 'src' / 'subdir' / 'utils.py').touch()
            (root / 'tests' / 'test_main.py').touch()
            (root / '__pycache__' / 'cached.pyc').touch()  # Should be excluded
            (root / '.git' / 'config').touch()  # Should be excluded
            (root / 'data' / 'data.txt').touch()  # Not a Python file
            (root / 'README.md').touch()  # Not a Python file
            
            # Create a file that matches exclusion pattern
            (root / 'src' / 'test_helper.py').touch()
            
            yield root

    def test_walk_returns_generator(self, temp_project_structure):
        """Verify that walk_python_files returns a generator."""
        result = walk_python_files(str(temp_project_structure))
        # Generators have __next__ method
        assert hasattr(result, '__next__')
        # Can convert to list
        files = list(result)
        assert isinstance(files, list)

    def test_walk_finds_python_files(self, temp_project_structure):
        """Verify that .py files are found."""
        files = list(walk_python_files(str(temp_project_structure)))
        py_files = [f for f in files if f.suffix == '.py']
        
        assert len(py_files) == 4  # main.py, module.py, utils.py, test_main.py
        
        file_names = {f.name for f in py_files}
        assert 'main.py' in file_names
        assert 'module.py' in file_names
        assert 'utils.py' in file_names
        assert 'test_main.py' in file_names

    def test_walk_excludes_pycache(self, temp_project_structure):
        """Verify that __pycache__ directories are excluded."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        # No files should be from __pycache__
        for f in files:
            assert '__pycache__' not in str(f)

    def test_walk_excludes_git(self, temp_project_structure):
        """Verify that .git directories are excluded."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        for f in files:
            assert '.git' not in str(f)

    def test_walk_excludes_venv(self, temp_project_structure):
        """Verify that venv directories are excluded."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        for f in files:
            assert 'venv' not in f.parts

    def test_walk_excludes_non_python_files(self, temp_project_structure):
        """Verify that non-.py files are not included."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        for f in files:
            assert f.suffix == '.py'
        
        # Verify no .txt or .md files
        file_names = {f.name for f in files}
        assert 'data.txt' not in file_names
        assert 'README.md' not in file_names
        assert 'cached.pyc' not in file_names

    def test_walk_with_custom_exclude_dirs(self, temp_project_structure):
        """Verify custom directory exclusion works."""
        # Exclude 'tests' directory
        files = list(walk_python_files(
            str(temp_project_structure),
            exclude_dirs={'tests'}
        ))
        
        for f in files:
            assert 'tests' not in f.parts
        
        # test_main.py should not be found
        file_names = {f.name for f in files}
        assert 'test_main.py' not in file_names

    def test_walk_with_custom_exclude_patterns(self, temp_project_structure):
        """Verify custom filename pattern exclusion works."""
        # Exclude files matching 'test_*'
        files = list(walk_python_files(
            str(temp_project_structure),
            exclude_patterns={'test_'}
        ))
        
        for f in files:
            assert not f.name.startswith('test_')
        
        # test_main.py should not be found
        file_names = {f.name for f in files}
        assert 'test_main.py' not in file_names

    def test_collect_python_files(self, temp_project_structure):
        """Verify collect_python_files returns a list of paths."""
        files = collect_python_files(str(temp_project_structure))
        
        assert isinstance(files, list)
        assert len(files) == 4
        assert all(isinstance(f, Path) for f in files)

    def test_count_python_files(self, temp_project_structure):
        """Verify count_python_files returns correct count."""
        count = count_python_files(str(temp_project_structure))
        assert count == 4

    def test_nonexistent_directory_raises_exception(self):
        """Verify FileWalkerException is raised for non-existent directory."""
        with pytest.raises(FileWalkerException):
            list(walk_python_files('/nonexistent/path/12345'))

    def test_file_path_is_directory_raises_exception(self):
        """Verify FileWalkerException is raised when path is a file."""
        with tempfile.NamedTemporaryFile() as tmp:
            with pytest.raises(FileWalkerException):
                list(walk_python_files(tmp.name))

    def test_empty_directory_returns_empty_generator(self, temp_project_structure):
        """Verify empty directory returns empty generator."""
        empty_dir = temp_project_structure / 'empty'
        empty_dir.mkdir()
        
        files = list(walk_python_files(str(empty_dir)))
        assert len(files) == 0

    def test_nested_directories_are_traversed(self, temp_project_structure):
        """Verify nested directories are traversed."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        # Should find files in nested subdirs
        file_paths = [str(f) for f in files]
        
        assert any('subdir' in p for p in file_paths)
        assert any('utils.py' in p for p in file_paths)

    def test_returns_path_objects(self, temp_project_structure):
        """Verify that yielded items are Path objects."""
        result = walk_python_files(str(temp_project_structure))
        first_file = next(result)
        
        assert isinstance(first_file, Path)
        assert first_file.exists()
        assert first_file.is_file()

    def test_multiple_calls_to_walk(self, temp_project_structure):
        """Verify that walk can be called multiple times."""
        files1 = list(walk_python_files(str(temp_project_structure)))
        files2 = list(walk_python_files(str(temp_project_structure)))
        
        assert len(files1) == len(files2)
        assert set(str(f) for f in files1) == set(str(f) for f in files2)

    def test_exclude_pattern_with_wildcard(self, temp_project_structure):
        """Verify pattern matching works for substring exclusion."""
        # Exclude any file containing 'test'
        files = list(walk_python_files(
            str(temp_project_structure),
            exclude_patterns={'test'}
        ))
        
        for f in files:
            assert 'test' not in f.name.lower()
        
        # Both test_main.py and test_helper.py should be excluded
        file_names = {f.name for f in files}
        assert 'test_main.py' not in file_names
        assert 'test_helper.py' not in file_names

    def test_default_exclusions_include_pycache(self, temp_project_structure):
        """Verify __pycache__ is excluded by default."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        for f in files:
            assert '__pycache__' not in str(f)

    def test_default_exclusions_include_git(self, temp_project_structure):
        """Verify .git is excluded by default."""
        files = list(walk_python_files(str(temp_project_structure)))
        
        for f in files:
            assert '.git' not in str(f)