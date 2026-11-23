"""
Unit tests for the create_state_directories module.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
# Assuming this test is run from the project root or via pytest discovery
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.setup.create_state_directories import create_directory

class TestCreateDirectory:
    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new_state" / "projects"
        assert not new_dir.exists()
        result = create_directory(new_dir)
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_existing_directory(self, tmp_path):
        """Test that creating an existing directory returns True and doesn't error."""
        existing_dir = tmp_path / "existing_state"
        existing_dir.mkdir(parents=True)
        assert existing_dir.exists()
        result = create_directory(existing_dir)
        assert result is True
        assert existing_dir.exists()

    def test_create_nested_directories(self, tmp_path):
        """Test creating deeply nested directories."""
        nested_dir = tmp_path / "a" / "b" / "c" / "d"
        assert not nested_dir.exists()
        result = create_directory(nested_dir)
        assert result is True
        assert nested_dir.exists()

    def test_permission_error_simulation(self, tmp_path):
        """
        Test behavior when directory creation might fail (e.g., permission issues).
        We simulate this by making a parent file where a directory is expected,
        which should cause mkdir to fail.
        """
        # Create a file where we want a directory
        blocker = tmp_path / "file_instead_of_dir"
        blocker.touch()
        
        # Try to create a directory with the same name
        result = create_directory(blocker)
        assert result is False