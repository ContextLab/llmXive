"""
Unit tests for the project setup script.
Verifies that the required directory structure is created correctly.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# Note: We need to adjust the import path based on how the test is run
# Assuming tests are run from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import create_directories


def test_create_directories_creates_all_required_paths():
    """Test that create_directories creates all required directories."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Call the function
            create_directories()

            # Verify each required directory exists
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "outputs",
                "tests",
                "contracts",
                ".github/workflows",
            ]

            for dir_name in required_dirs:
                dir_path = Path(temp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"

        finally:
            os.chdir(original_cwd)


def test_create_directories_idempotent():
    """Test that running create_directories multiple times is safe."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Run twice
            create_directories()
            create_directories()

            # All directories should still exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "outputs",
                "tests",
                "contracts",
                ".github/workflows",
            ]

            for dir_name in required_dirs:
                dir_path = Path(temp_dir) / dir_name
                assert dir_path.exists(), f"Directory {dir_path} missing after second run"

        finally:
            os.chdir(original_cwd)