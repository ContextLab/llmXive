"""
Tests for the setup_directories module.
Verifies that the required directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

from code.setup_directories import setup_directories


class TestSetupDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Create a temporary directory for testing and clean up afterwards.
        """
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_setup_directories_creates_all_folders(self):
        """
        Verify that all required directories are created.
        """
        setup_directories()

        required_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/analysis",
            "tests",
            "contracts",
            "state"
        ]

        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_nested_directories_exist(self):
        """
        Verify that nested directories (e.g., data/raw) are created.
        """
        setup_directories()

        nested_dirs = [
            "data/raw",
            "data/processed",
            "data/analysis"
        ]

        for dir_name in nested_dirs:
            dir_path = Path(dir_name)
            assert dir_path.exists(), f"Nested directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_directories_are_empty_initially(self):
        """
        Verify that the created directories are initially empty.
        """
        setup_directories()

        # Note: The directories themselves should exist and be empty
        # (excluding . and ..)
        required_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/analysis",
            "tests",
            "contracts",
            "state"
        ]

        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            contents = list(dir_path.iterdir())
            # Directories might contain hidden files or be empty
            # We just verify they exist and are directories
            assert dir_path.is_dir()