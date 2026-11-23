"""
Tests for directory setup (T001a).
These tests verify that the setup script creates the required directories.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the setup function
# We need to adjust the import path since this is in tests/unit
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project_dirs import create_directory, verify_directory


class TestDirectoryCreation:
    """Test cases for directory creation and verification."""

    def test_create_directory_new(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new_test_dir"
        assert not new_dir.exists()
        result = create_directory(new_dir)
        assert result is True
        assert new_dir.is_dir()

    def test_create_directory_exists(self, tmp_path):
        """Test creating a directory that already exists."""
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()
        assert existing_dir.is_dir()
        result = create_directory(existing_dir)
        assert result is True  # Should succeed with exist_ok=True
        assert existing_dir.is_dir()

    def test_verify_directory_exists(self, tmp_path):
        """Test verifying an existing directory."""
        test_dir = tmp_path / "test_verify"
        test_dir.mkdir()
        assert verify_directory(test_dir) is True

    def test_verify_directory_not_exists(self, tmp_path):
        """Test verifying a non-existing directory."""
        non_existent = tmp_path / "does_not_exist"
        assert verify_directory(non_existent) is False

    def test_create_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        result = create_directory(nested_dir)
        assert result is True
        assert nested_dir.is_dir()
        assert (tmp_path / "level1").is_dir()
        assert (tmp_path / "level1" / "level2").is_dir()

    def test_project_structure_simulation(self, tmp_path):
        """Simulate the T001a task by creating the expected project structure."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Recreate the logic from setup_project_dirs.main()
            directories = [
                tmp_path / "code",
                tmp_path / "data",
                tmp_path / "results",
                tmp_path / "tests",
            ]

            # Create directories
            for directory in directories:
                create_directory(directory)

            # Verify directories
            for directory in directories:
                assert verify_directory(directory), f"Directory {directory} was not created"
            
            # Verify using os.path.isdir as a secondary check
            for directory in directories:
                assert os.path.isdir(directory), f"os.path.isdir check failed for {directory}"

        finally:
            os.chdir(original_cwd)