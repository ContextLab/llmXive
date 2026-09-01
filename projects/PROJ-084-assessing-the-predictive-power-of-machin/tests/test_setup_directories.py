"""
Unit tests for the setup_directories script.
Verifies that the required directories are created.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We import the function to test, but since setup_directories.py is in code/,
# we need to ensure the path is correct or run tests from the root.
# Assuming tests are run from the project root.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main

def test_directories_created(tmp_path):
    """Test that the script creates the required directories."""
    # Change to a temporary directory to avoid polluting the real project
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Run the setup function
        main()

        # Verify directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests"
        ]

        for dir_name in required_dirs:
            target_path = tmp_path / dir_name
            assert target_path.exists(), f"Directory {target_path} was not created"
            assert target_path.is_dir(), f"{target_path} exists but is not a directory"

    finally:
        os.chdir(original_cwd)