"""
Tests for the setup_directories module.
Verifies that the required directories are created correctly.
"""
import os
import tempfile
from pathlib import Path

import pytest

# Import the function to test
# Note: The import path assumes this test file is in tests/
# and the code is in code/setup_directories.py relative to project root.
# We will mock the base path to test in a temporary directory.
from setup_directories import create_directories


def test_create_directories_creates_all_required_folders():
    """Test that all required data and code directories are created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)

        # Call the function
        create_directories(base_path)

        # Expected data directories
        expected_data_dirs = [
            "data/raw-fmri",
            "data/processed-fmri",
            "data/behavioral",
            "data/results",
        ]

        # Expected code directories
        expected_code_dirs = [
            "code/manipulation",
            "code/utils",
        ]

        # Verify data directories exist and contain .gitkeep
        for dir_name in expected_data_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} is not a directory."
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep file missing in {dir_path}."

        # Verify code directories exist and contain .gitkeep
        for dir_name in expected_code_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"{dir_path} is not a directory."
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep file missing in {dir_path}."


def test_create_directories_idempotent():
    """Test that running create_directories multiple times doesn't raise errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)

        # Run twice
        create_directories(base_path)
        create_directories(base_path)

        # Verify directories still exist
        assert (base_path / "data/raw-fmri").exists()
        assert (base_path / "code/manipulation").exists()