"""
Tests for the setup_directories module (T001a).
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from code.setup_directories import main

def test_directory_creation(tmp_path):
    """
    Test that main() creates the required directories in the specified location.
    We change the current working directory to a temporary directory to avoid
    modifying the actual project root during tests.
    """
    # Save original cwd
    original_cwd = os.getcwd()

    try:
        # Change to temporary directory
        os.chdir(str(tmp_path))

        # Run the setup script
        result = main()

        # Verify return code is 0
        assert result == 0, "main() should return 0 on success"

        # Verify directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs"
        ]

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    finally:
        # Restore original cwd
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """
    Test that running main() multiple times does not cause errors
    and doesn't duplicate directories.
    """
    original_cwd = os.getcwd()

    try:
        os.chdir(str(tmp_path))

        # Run twice
        result1 = main()
        result2 = main()

        assert result1 == 0
        assert result2 == 0

        # Verify directories still exist and are single instances
        required_dirs = ["code", "data/raw", "data/processed", "results", "specs"]
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists()
            assert dir_path.is_dir()
            # Check that it's a single directory, not duplicated
            assert len(list(tmp_path.glob(f"{dir_name}"))) == 1

    finally:
        os.chdir(original_cwd)