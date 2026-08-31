"""
Tests for the setup_data_directories module (T004).

These tests verify that the required directory structure is created correctly.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from setup_data_directories import setup_data_directories


class TestSetupDataDirectories:
    """Test cases for setup_data_directories function."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Run the setup on a temporary directory
        created_dirs = setup_data_directories(str(tmp_path))
        
        # Check that we got the expected number of directories
        assert len(created_dirs) == 3
        
        # Verify each directory exists
        expected_subdirs = ["data/raw", "data/processed", "state"]
        for subdir in expected_subdirs:
            expected_path = tmp_path / subdir
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"Path {expected_path} is not a directory"

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        # The function should create data/ and state/ if they don't exist
        created_dirs = setup_data_directories(str(tmp_path))
        
        # Check that data/ and state/ parent directories exist
        data_dir = tmp_path / "data"
        state_dir = tmp_path / "state"
        
        assert data_dir.exists()
        assert state_dir.exists()

    def test_idempotent_creation(self, tmp_path):
        """Test that running the function twice doesn't cause errors."""
        # First run
        created_dirs_1 = setup_data_directories(str(tmp_path))
        
        # Second run should succeed without errors
        created_dirs_2 = setup_data_directories(str(tmp_path))
        
        # Should create the same directories
        assert len(created_dirs_1) == len(created_dirs_2)
        
        # All directories should still exist
        for dir_path in created_dirs_2:
            assert Path(dir_path).exists()

    def test_returns_absolute_paths(self, tmp_path):
        """Test that the function returns absolute paths."""
        created_dirs = setup_data_directories(str(tmp_path))
        
        for dir_path in created_dirs:
            assert os.path.isabs(dir_path), f"Path {dir_path} is not absolute"

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles pre-existing directories gracefully."""
        # Create some directories manually
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "state").mkdir(parents=True)
        
        # Running setup should not fail
        created_dirs = setup_data_directories(str(tmp_path))
        
        assert len(created_dirs) == 3

    def test_uses_correct_project_root(self, tmp_path):
        """Test that the function respects the provided project_root argument."""
        custom_root = tmp_path / "custom"
        custom_root.mkdir()
        
        created_dirs = setup_data_directories(str(custom_root))
        
        # Verify paths are under custom_root
        for dir_path in created_dirs:
            assert dir_path.startswith(str(custom_root)), \
                f"Directory {dir_path} is not under {custom_root}"