"""
Unit tests to verify the project directory structure exists.

This test file validates that T001 has been successfully implemented
by checking for the existence of all required directories.
"""
import os
import sys
from pathlib import Path
import unittest

# Add the project root to the path to allow imports if needed
# (though this test primarily uses os/pathlib directly)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

class TestProjectStructure(unittest.TestCase):
    """Tests for verifying the project directory structure."""

    def setUp(self):
        """Set up the test environment."""
        self.base_path = project_root
        self.required_dirs = [
            "code",
            "code/extraction",
            "code/inference",
            "code/analysis",
            "code/utils",
            "data/raw",
            "data/extracted",
            "data/aggregated",
            "data/results",
            "data/models",
            "tests/unit",
            "tests/integration"
        ]

    def test_all_directories_exist(self):
        """Verify that all required directories exist."""
        missing_dirs = []
        for dir_path in self.required_dirs:
            full_path = self.base_path / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
            elif not full_path.is_dir():
                missing_dirs.append(f"{dir_path} (exists but is not a directory)")

        self.assertEqual(len(missing_dirs), 0, f"Missing directories: {missing_dirs}")

    def test_code_directory_is_writable(self):
        """Verify that the code directory and its subdirectories are writable."""
        code_dir = self.base_path / "code"
        self.assertTrue(code_dir.exists(), "code/ directory does not exist")
        self.assertTrue(os.access(code_dir, os.W_OK), "code/ directory is not writable")

    def test_data_directory_is_writable(self):
        """Verify that the data directory and its subdirectories are writable."""
        data_dir = self.base_path / "data"
        self.assertTrue(data_dir.exists(), "data/ directory does not exist")
        self.assertTrue(os.access(data_dir, os.W_OK), "data/ directory is not writable")

    def test_tests_directory_is_writable(self):
        """Verify that the tests directory and its subdirectories are writable."""
        tests_dir = self.base_path / "tests"
        self.assertTrue(tests_dir.exists(), "tests/ directory does not exist")
        self.assertTrue(os.access(tests_dir, os.W_OK), "tests/ directory is not writable")

if __name__ == "__main__":
    unittest.main()