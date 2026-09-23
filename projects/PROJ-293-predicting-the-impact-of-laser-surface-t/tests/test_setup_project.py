import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_project import main

class TestSetupProject:
    """Tests for T001: Project structure creation."""

    def test_creates_required_directories(self, tmp_path):
        """Verify that the script creates all required directories."""
        # Change to the temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup script
            result = main()
            
            # Assert exit code is 0
            assert result == 0

            # Define expected directories
            expected_dirs = [
                "code",
                "data",
                "tests",
                "state",
                "models",
                "data/raw",
                "data/processed",
                "reports"
            ]

            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        """Verify that running the script twice does not cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup script twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0

            # Verify directories still exist
            expected_dirs = ["code", "data", "tests", "state", "models", "reports"]
            for dir_name in expected_dirs:
                assert (tmp_path / dir_name).exists()

        finally:
            os.chdir(original_cwd)