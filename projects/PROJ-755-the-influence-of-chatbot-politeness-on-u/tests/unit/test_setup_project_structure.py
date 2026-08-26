import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to allow importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_structure

class TestProjectStructure:
    """
    Unit tests for the project structure creation logic.
    These tests verify that the required directories are created or confirmed to exist.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """
        Set up a temporary directory for testing to avoid polluting the real project structure.
        We change the working directory to the temp path for the duration of the test.
        """
        self.original_cwd = Path.cwd()
        os.chdir(tmp_path)
        yield tmp_path
        os.chdir(self.original_cwd)

    def test_creates_required_directories(self, tmp_path):
        """
        Verify that create_structure() creates all required directories.
        """
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/utils",
            "tests",
            "tests/contract",
            "tests/unit",
            "tests/integration",
            "docs",
            "state"
        ]

        # Run the structure creation
        create_structure()

        # Verify each directory exists
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created."
            assert dir_path.is_dir(), f"Path {dir_name} exists but is not a directory."

    def test_handles_existing_directories(self, tmp_path):
        """
        Verify that create_structure() does not fail if directories already exist.
        """
        required_dirs = [
            "data/raw",
            "code"
        ]

        # Pre-create some directories
        for dir_name in required_dirs:
            (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Run the structure creation - should not raise an exception
        create_structure()

        # Verify they still exist
        for dir_name in required_dirs:
            assert (tmp_path / dir_name).exists()
