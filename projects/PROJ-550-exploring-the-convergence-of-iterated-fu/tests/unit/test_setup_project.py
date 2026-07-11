import os
import pytest
from pathlib import Path
import shutil

# Import the function to test
import sys
sys.path.insert(0, 'code')
from setup_project import main

class TestSetupProject:
    PROJECT_NAME = "PROJ-550-exploring-the-convergence-of-iterated-fu"
    BASE_PATH = Path("projects") / PROJECT_NAME

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure clean state before test and cleanup after."""
        # Cleanup if exists
        if self.BASE_PATH.exists():
            shutil.rmtree(self.BASE_PATH)
        yield
        # Cleanup after test
        if self.BASE_PATH.exists():
            shutil.rmtree(self.BASE_PATH)

    def test_t001_creates_directory_structure(self):
        """
        Verify T001: Create project structure.
        Checks that the specific subdirectories exist after running main().
        """
        required_subdirs = [
            "code",
            "data/raw",
            "data/derived",
            "tests/unit",
            "tests/contract",
            "docs"
        ]

        # Execute the setup
        result = main()
        assert result == 0, "setup_project.main() should return 0 on success"

        # Verify root exists
        assert self.BASE_PATH.exists(), f"Project root {self.BASE_PATH} should exist"
        assert self.BASE_PATH.is_dir(), f"Project root {self.BASE_PATH} should be a directory"

        # Verify each subdirectory
        for subdir in required_subdirs:
            dir_path = self.BASE_PATH / subdir
            assert dir_path.exists(), f"Subdirectory {dir_path} should exist"
            assert dir_path.is_dir(), f"Path {dir_path} should be a directory"

        # Verify nested structure (e.g., data/raw exists as a path)
        assert (self.BASE_PATH / "data" / "raw").exists(), "data/raw path should exist"
        assert (self.BASE_PATH / "data" / "derived").exists(), "data/derived path should exist"
        assert (self.BASE_PATH / "tests" / "unit").exists(), "tests/unit path should exist"
        assert (self.BASE_PATH / "tests" / "contract").exists(), "tests/contract path should exist"