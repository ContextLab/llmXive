import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# Since setup_project.py is in code/, we need to adjust path or import properly
# For this test, we assume the test runner adds 'code' to sys.path or we import via relative path logic
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import main

def test_setup_project_creates_directories(tmp_path):
    """
    Verify that setup_project creates the required directory structure.
    """
    # Change to a temporary directory to avoid cluttering the real project during test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run the setup script
        result = main()

        # Assert the script reported success
        assert result == 0, "setup_project main() should return 0 on success"

        # Define expected directories
        expected_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/utils",
            "tests",
            "results/paper_figures",
        ]

        # Verify each directory actually exists on disk
        for dir_path in expected_dirs:
            full_path = Path(dir_path)
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"Path {full_path} exists but is not a directory"

    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_setup_project_idempotent(tmp_path):
    """
    Verify that running setup_project twice does not cause errors.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run once
        result1 = main()
        assert result1 == 0

        # Run again
        result2 = main()
        assert result2 == 0

    finally:
        os.chdir(original_cwd)