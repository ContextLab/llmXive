"""
Tests for the project setup script (T001).
Verifies that the directory structure is created correctly and the log file exists.
"""
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add the code directory to the path so we can import setup_project
# Assuming this test file is at tests/test_setup.py and code is at code/
# We need to adjust sys.path to import from code/
current_dir = Path(__file__).parent
code_dir = current_dir.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import create_directory_structure, write_setup_log


class TestProjectSetup(unittest.TestCase):
    """Test cases for project directory initialization."""

    def setUp(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_root = os.path.join(self.temp_dir, "PROJ-308-test")

    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_directory_structure(self):
        """Test that create_directory_structure creates all required folders."""
        success = create_directory_structure(self.test_project_root)

        self.assertTrue(success, "Directory creation should return True")

        # Check for the existence of all required directories
        required_dirs = [
            "code", "data", "state", "tests", "docs",
            "data/raw", "data/processed",
            "tests/unit", "tests/integration",
            "state/projects", "tools", "reviews"
        ]

        for d in required_dirs:
            full_path = os.path.join(self.test_project_root, d)
            self.assertTrue(
                os.path.isdir(full_path),
                f"Directory {d} should exist"
            )

    def test_write_setup_log(self):
        """Test that write_setup_log creates the log file with correct content."""
        # First create the directories
        create_directory_structure(self.test_project_root)

        # Then write the log
        write_setup_log(self.test_project_root)

        log_path = os.path.join(self.test_project_root, "setup_log.txt")
        self.assertTrue(os.path.isfile(log_path), "setup_log.txt should be created")

        with open(log_path, 'r') as f:
            content = f.read()

        # Verify key content
        self.assertIn("Status: SUCCESS", content, "Log should indicate success")
        self.assertIn("Verification complete", content, "Log should end with verification message")

        # Check that at least one directory is marked OK
        self.assertIn("[OK]", content, "Log should show at least one successful directory")

    def test_full_workflow(self):
        """Test the complete workflow: create dirs + write log + verify."""
        success = create_directory_structure(self.test_project_root)
        self.assertTrue(success)

        write_setup_log(self.test_project_root)

        # Verify the log file exists and is readable
        log_path = os.path.join(self.test_project_root, "setup_log.txt")
        self.assertTrue(os.path.exists(log_path))

        # Verify all directories exist
        required_dirs = [
            "code", "data", "state", "tests", "docs",
            "data/raw", "data/processed",
            "tests/unit", "tests/integration",
            "state/projects", "tools", "reviews"
        ]

        for d in required_dirs:
            self.assertTrue(
                os.path.isdir(os.path.join(self.test_project_root, d)),
                f"{d} must exist"
            )


if __name__ == "__main__":
    unittest.main()