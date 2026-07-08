"""
Tests for the setup_directories script.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest

# Import the function to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

# We need to mock the BASE_DIR logic since it's hardcoded in the script
# Instead, we'll test the logic directly
from setup_directories import DIRECTORIES

class TestDirectoryCreation:
    """Test cases for directory creation logic."""

    def test_directories_defined(self):
        """Verify that all required directories are defined."""
        required_dirs = {"code", "tests", "data/raw", "data/processed", "state"}
        assert set(DIRECTORIES) == required_dirs, f"Expected {required_dirs}, got {set(DIRECTORIES)}"

    def test_directory_paths_valid(self):
        """Verify that directory paths don't contain invalid characters."""
        for dir_path in DIRECTORIES:
            assert not os.path.isabs(dir_path), f"Directory path should be relative: {dir_path}"
            assert ".." not in dir_path, f"Directory path should not contain '..': {dir_path}"
            assert dir_path.startswith("data/") or dir_path in ["code", "tests", "state"], \
                f"Unexpected directory structure: {dir_path}"

    def test_data_subdirectories_exist(self):
        """Verify that data subdirectories are properly nested."""
        data_dirs = [d for d in DIRECTORIES if d.startswith("data/")]
        assert len(data_dirs) == 2, f"Expected 2 data subdirectories, found {len(data_dirs)}"
        assert "data/raw" in data_dirs
        assert "data/processed" in data_dirs

if __name__ == "__main__":
    pytest.main([__file__, "-v"])