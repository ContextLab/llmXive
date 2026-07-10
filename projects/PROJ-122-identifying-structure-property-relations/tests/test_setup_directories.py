"""
Unit tests for the setup_directories.py script.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to simulate the script being run or import the logic
# Since the script is in code/, we need to add it to path or copy logic
# For this test, we will import the logic directly if possible, or mock the execution.
# To keep it simple and robust, we will test the logic by recreating it in the test or importing.
# Let's assume we can import from code.setup_directories if we add code to path.

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories

class TestDirectoryCreation:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary directory to simulate project root."""
        return tmp_path

    def test_creates_required_dirs(self, temp_project_root):
        """Test that all required directories are created."""
        # Change to temp root to simulate project root execution
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            
            # Call the function
            created, skipped = create_directories()
            
            # Verify directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/features",
                "tests",
                "state/projects"
            ]
            
            for dir_name in required_dirs:
                dir_path = temp_project_root / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
            
            # Verify count
            assert created == len(required_dirs)
            assert skipped == 0
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_dirs(self, temp_project_root):
        """Test that the script handles existing directories gracefully."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            
            # Pre-create one directory
            (temp_project_root / "code").mkdir()
            
            # Call the function
            created, skipped = create_directories()
            
            # Verify count
            assert created == len(["code", "data/raw", "data/processed", "data/features", "tests", "state/projects"]) - 1
            assert skipped == 1
            
            # Verify all still exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/features",
                "tests",
                "state/projects"
            ]
            for dir_name in required_dirs:
                assert (temp_project_root / dir_name).exists()
        finally:
            os.chdir(original_cwd)