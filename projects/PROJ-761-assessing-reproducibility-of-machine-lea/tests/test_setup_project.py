import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path to allow imports from code/
# Assuming tests are in tests/ and code is in code/
# We need to import from code/setup_project
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import main

class TestSetupProject:
    """Test suite for the project setup script."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to the temporary directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup function
            result = main()
            
            # Check return code
            assert result == 0, "Setup script should return 0 on success"
            
            # Define expected directories
            expected_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "artifacts/logs",
                "artifacts/plots",
                "artifacts/reports",
                "contracts"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
        
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        """Verify that running the script twice does not cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run setup twice
            result1 = main()
            result2 = main()
            
            assert result1 == 0
            assert result2 == 0
            
            # Verify directories still exist
            expected_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "artifacts/logs",
                "artifacts/plots",
                "artifacts/reports",
                "contracts"
            ]
            
            for dir_name in expected_dirs:
                assert (tmp_path / dir_name).exists()
        finally:
            os.chdir(original_cwd)