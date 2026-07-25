"""
Unit tests for setup_directories.py functionality.
Verifies that the directory structure is created correctly.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_directories import setup_directories, DATA_DIRS, TEST_DIRS


class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to simulate project root."""
        self.temp_dir = tempfile.mkdtemp()
        # Monkey patch PROJECT_ROOT for testing
        import setup_directories
        self.original_root = setup_directories.PROJECT_ROOT
        setup_directories.PROJECT_ROOT = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
        import setup_directories
        setup_directories.PROJECT_ROOT = self.original_root

    def test_data_directories_created(self):
        """Test that all data directories are created."""
        setup_directories()

        for dir_path in DATA_DIRS:
            full_path = Path(self.temp_dir) / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_path} is not a directory")

    def test_test_directories_created(self):
        """Test that all test directories are created."""
        setup_directories()

        for dir_path in TEST_DIRS:
            full_path = Path(self.temp_dir) / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_path} is not a directory")

    def test_idempotency(self):
        """Test that running setup multiple times doesn't cause errors."""
        # Run twice
        setup_directories()
        setup_directories()

        # Verify all directories still exist
        all_dirs = DATA_DIRS + TEST_DIRS
        for dir_path in all_dirs:
            full_path = Path(self.temp_dir) / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} missing after second run")


if __name__ == "__main__":
    unittest.main()