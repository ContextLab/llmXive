import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import main

def test_directory_creation():
    """
    Test that the setup_project script creates the required directory structure.
    This test creates a temporary directory, runs the main function there,
    and verifies the existence of all required subdirectories.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the setup function
            exit_code = main()
            
            # Verify exit code
            assert exit_code == 0, "Setup script should return 0"
            
            # Define expected directories
            expected_dirs = [
                "data/raw",
                "data/processed",
                "data/ground_truth",
                "data/logs",
                "code/utils",
                "tests/unit",
                "tests/contract",
                "docs/paper",
                "scripts"
            ]
            
            # Verify each directory exists
            for dir_name in expected_dirs:
                dir_path = Path(tmp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"Path {dir_name} is not a directory"
                
        finally:
            os.chdir(original_cwd)

def test_no_error_on_rerun():
    """
    Test that running the setup script again does not raise errors
    (idempotency check).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run first time
            exit_code_1 = main()
            assert exit_code_1 == 0
            
            # Run second time
            exit_code_2 = main()
            assert exit_code_2 == 0
            
        finally:
            os.chdir(original_cwd)
