import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the functions to test
from setup.verify_structure import check_directory_writable, REQUIRED_DIRS, PROJECT_ROOT

class TestVerifyStructure:
    
    def test_check_directory_writable_existing(self, tmp_path):
        """Test that an existing, writable directory returns True."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        assert check_directory_writable(test_dir) is True

    def test_check_directory_writable_nonexistent(self, tmp_path):
        """Test that a non-existent directory returns False."""
        test_dir = tmp_path / "nonexistent"
        assert check_directory_writable(test_dir) is False

    def test_check_directory_writable_file_instead_of_dir(self, tmp_path):
        """Test that a path pointing to a file returns False."""
        test_file = tmp_path / "test_file.txt"
        test_file.touch()
        assert check_directory_writable(test_file) is False

    def test_required_dirs_constant(self):
        """Test that REQUIRED_DIRS is a non-empty list."""
        assert isinstance(REQUIRED_DIRS, list)
        assert len(REQUIRED_DIRS) > 0
        assert "code" in REQUIRED_DIRS
        assert "data/raw" in REQUIRED_DIRS
        assert "tests" in REQUIRED_DIRS

    def test_project_root_exists(self):
        """Test that PROJECT_ROOT is a valid Path object."""
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()