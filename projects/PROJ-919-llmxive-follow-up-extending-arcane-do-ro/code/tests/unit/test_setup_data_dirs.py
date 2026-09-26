import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path to allow imports
code_path = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from scripts.setup_data_dirs import setup_directories, REQUIRED_DIRS

class TestDataDirectories:
    """
    Unit tests for the data directory setup functionality.
    """

    def test_setup_directories_creates_missing_dirs(self, tmp_path):
        """
        Test that setup_directories creates the required directories if they don't exist.
        """
        # Ensure the directories don't exist yet in the temp path
        for dir_name in REQUIRED_DIRS:
            assert not (tmp_path / dir_name).exists()

        # Run the setup
        setup_directories(tmp_path)

        # Verify all directories were created
        for dir_name in REQUIRED_DIRS:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_setup_directories_skips_existing_dirs(self, tmp_path):
        """
        Test that setup_directories does not fail if directories already exist.
        """
        # Pre-create one of the required directories
        existing_dir = tmp_path / REQUIRED_DIRS[0]
        existing_dir.mkdir(parents=True)

        # Run the setup
        setup_directories(tmp_path)

        # Verify the directory still exists and is a directory
        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_setup_directories_creates_nested_structure(self, tmp_path):
        """
        Test that nested directories (e.g., data/gold_standard) are created correctly.
        """
        # Run the setup
        setup_directories(tmp_path)

        # Check specific nested paths
        nested_paths = [
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "artifacts"
        ]
        for path_str in nested_paths:
            assert (tmp_path / path_str).exists()

    def test_required_dirs_constant(self):
        """
        Test that the REQUIRED_DIRS constant contains the expected paths.
        """
        expected_dirs = {
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "artifacts"
        }
        assert set(REQUIRED_DIRS) == expected_dirs, "REQUIRED_DIRS constant does not match expected structure"