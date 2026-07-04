"""
Unit tests for the setup_dirs.py script functionality.
Verifies that the expected directory structure is created.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the main logic function from the setup script
# We assume setup_dirs.py is in the parent directory of tests/unit
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_dirs import main


def test_directory_creation(tmp_path):
    """Test that the script creates the required directories."""
    # Change to the temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run the main function which creates directories
        # Note: The script uses Path(".").resolve() which will be tmp_path
        result = main()

        # Check return code
        assert result == 0, "Setup script should return 0 on success"

        # Verify directories exist
        expected_dirs = [
            "code",
            "data",
            "tests",
            "docs",
            "data/raw",
            "data/processed",
            "data/results",
        ]

        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"Path {dir_name} should be a directory"

    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def test_idempotency(tmp_path):
    """Test that running the script twice doesn't cause errors."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run once
        result1 = main()
        assert result1 == 0

        # Run again
        result2 = main()
        assert result2 == 0

        # Verify directories still exist
        expected_dirs = ["code", "data", "tests", "docs"]
        for dir_name in expected_dirs:
            assert (tmp_path / dir_name).exists()

    finally:
        os.chdir(original_cwd)