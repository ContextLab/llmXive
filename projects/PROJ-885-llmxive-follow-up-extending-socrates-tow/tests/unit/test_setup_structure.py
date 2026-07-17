"""
Unit tests for the project setup script.
Verifies that the required directory structure is created correctly.
"""

import os
import shutil
import tempfile
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_project_structure import DIRECTORIES, create_directories

class TestProjectStructure:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory and change to it for testing."""
        # Save current directory
        self.original_dir = os.getcwd()
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        # Change to the temporary directory
        os.chdir(self.temp_dir)
        yield
        # Restore original directory
        os.chdir(self.original_dir)
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def test_directories_list(self):
        """Test that the DIRECTORIES constant contains the expected paths."""
        expected_dirs = {
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
            "contracts",
        }
        actual_dirs = set(DIRECTORIES)
        # Check that all expected directories are in the list
        assert expected_dirs.issubset(actual_dirs), f"Missing directories: {expected_dirs - actual_dirs}"

    def test_create_directories_creates_all(self):
        """Test that create_directories actually creates the directories."""
        create_directories()

        for dir_path in DIRECTORIES:
            assert os.path.exists(dir_path), f"Directory {dir_path} was not created"
            assert os.path.isdir(dir_path), f"{dir_path} exists but is not a directory"

    def test_create_directories_idempotent(self):
        """Test that running create_directories twice does not cause errors."""
        # Run twice
        result1 = create_directories()
        result2 = create_directories()

        assert result1 is True
        assert result2 is True

        # Verify all directories still exist
        for dir_path in DIRECTORIES:
            assert os.path.exists(dir_path)
