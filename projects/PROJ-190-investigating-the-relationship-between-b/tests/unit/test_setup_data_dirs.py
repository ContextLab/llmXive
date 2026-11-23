"""
Unit tests for the data directory setup script.

These tests verify that:
1. The required directories are created.
2. Existing directories are handled gracefully.
3. The function returns the correct list of paths.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from setup_data_dirs import create_data_directories, REQUIRED_DIRS


class TestDataDirectoryCreation:
    """Tests for create_data_directories function."""

    def setup_method(self):
        """Set up a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_creates_required_directories(self):
        """Test that all required directories are created."""
        created_paths = create_data_directories(Path(self.temp_dir))
        
        # Verify we got the expected number of paths
        assert len(created_paths) == len(REQUIRED_DIRS)
        
        # Verify each required directory exists and is in the returned list
        for dir_name in REQUIRED_DIRS:
            expected_path = Path(self.temp_dir) / dir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path in created_paths, f"{expected_path} not in returned list"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"

    def test_handles_existing_directories(self):
        """Test that existing directories are not recreated or cause errors."""
        # Pre-create one of the directories
        pre_existing = Path(self.temp_dir) / REQUIRED_DIRS[0]
        pre_existing.mkdir(parents=True)
        
        # Run the function
        created_paths = create_data_directories(Path(self.temp_dir))
        
        # Should still return all paths (existing + new)
        assert len(created_paths) == len(REQUIRED_DIRS)
        
        # Verify the pre-existing directory is still there
        assert pre_existing.exists()
        assert pre_existing.is_dir()

    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist."""
        # The function should create 'data' if it doesn't exist
        created_paths = create_data_directories(Path(self.temp_dir))
        
        data_dir = Path(self.temp_dir) / "data"
        assert data_dir.exists(), "Parent 'data' directory was not created"
        assert data_dir.is_dir(), "Parent 'data' is not a directory"

    def test_returns_absolute_paths(self):
        """Test that returned paths are absolute."""
        created_paths = create_data_directories(Path(self.temp_dir))
        
        for path in created_paths:
            assert path.is_absolute(), f"Path {path} is not absolute"

    def test_empty_required_dirs_list(self):
        """Test behavior if REQUIRED_DIRS is empty (edge case)."""
        # This is a hypothetical test; in reality REQUIRED_DIRS is constant
        # but we verify the logic handles an empty list gracefully
        if not REQUIRED_DIRS:
            paths = create_data_directories(Path(self.temp_dir))
            assert len(paths) == 0