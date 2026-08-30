import os
import tempfile
import shutil
import pytest
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_project import main

def test_directory_creation(tmp_path):
    """
    Test that the setup script creates the required directory structure.
    We run the script in a temporary directory to verify file system changes.
    """
    # Change to the temp directory
    original_dir = os.getcwd()
    os.chdir(str(tmp_path))

    try:
        # Run the setup function
        exit_code = main()
        
        # Verify exit code
        assert exit_code == 0, "Setup script should exit with code 0"

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
        for dir_path in expected_dirs:
            full_path = os.path.join(str(tmp_path), dir_path)
            assert os.path.isdir(full_path), f"Directory {dir_path} was not created"

    finally:
        # Restore original directory
        os.chdir(original_dir)

def test_idempotency(tmp_path):
    """
    Test that running the script twice does not cause errors.
    """
    original_dir = os.getcwd()
    os.chdir(str(tmp_path))

    try:
        # Run twice
        exit_code_1 = main()
        exit_code_2 = main()

        assert exit_code_1 == 0
        assert exit_code_2 == 0

        # Verify structure still exists
        assert os.path.isdir("data/raw")
        assert os.path.isdir("contracts")
    finally:
        os.chdir(original_dir)