import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from setup_directories import ensure_directory

class TestEnsureDirectory:
    """Unit tests for the ensure_directory function."""

    def test_creates_new_directory(self, tmp_path):
        """Test that a new directory is created successfully."""
        new_dir = tmp_path / "new_subdir"
        ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_exits_gracefully_if_exists(self, tmp_path):
        """Test that the function does not fail if directory already exists."""
        existing_dir = tmp_path / "existing_subdir"
        existing_dir.mkdir()
        
        # Should not raise
        ensure_directory(existing_dir)
        assert existing_dir.exists()

    def test_creates_nested_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        ensure_directory(nested_dir)
        assert nested_dir.exists()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()

    def test_handles_permission_error(self, tmp_path):
        """Test behavior when directory creation is not permitted."""
        # Create a file where we want a directory
        blocking_file = tmp_path / "blocking_file"
        blocking_file.touch()
        
        with pytest.raises(Exception):
            # Trying to create a directory where a file exists should fail
            ensure_directory(blocking_file)
