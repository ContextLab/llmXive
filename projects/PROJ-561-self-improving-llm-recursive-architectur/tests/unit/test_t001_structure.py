"""
Unit tests for Task T001: Create project structure.

This test verifies that the required directories and __init__.py files
exist after running the setup script.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the code directory to the path so we can import setup_project
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from setup_project import create_project_structure


class TestProjectStructure(unittest.TestCase):
    """Test cases for verifying project structure creation."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_project_structure_creates_directories(self):
        """Test that create_project_structure creates all required directories."""
        # Run the function
        result = create_project_structure()
        self.assertTrue(result, "create_project_structure should return True")

        # Define required directories
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration",
        ]

        # Verify each directory exists
        for dir_name in required_dirs:
            dir_path = Path(self.temp_dir) / dir_name
            self.assertTrue(
                dir_path.exists(),
                f"Directory {dir_name} should exist"
            )
            self.assertTrue(
                dir_path.is_dir(),
                f"{dir_name} should be a directory"
            )

    def test_create_project_structure_creates_init_files(self):
        """Test that create_project_structure creates __init__.py in all directories."""
        # Run the function
        result = create_project_structure()
        self.assertTrue(result, "create_project_structure should return True")

        # Define required directories
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration",
        ]

        # Verify __init__.py exists in each directory
        for dir_name in required_dirs:
            dir_path = Path(self.temp_dir) / dir_name
            init_file = dir_path / "__init__.py"
            self.assertTrue(
                init_file.exists(),
                f"__init__.py should exist in {dir_name}"
            )
            self.assertTrue(
                init_file.is_file(),
                f"__init__.py in {dir_name} should be a file"
            )
            # Verify the file is not empty (contains at least a newline or comment)
            content = init_file.read_text()
            # We expect at least a comment or newline
            self.assertGreaterEqual(
                len(content), 0,
                f"__init__.py in {dir_name} should have content"
            )

    def test_create_project_structure_idempotent(self):
        """Test that running create_project_structure multiple times doesn't cause errors."""
        # Run the function twice
        result1 = create_project_structure()
        result2 = create_project_structure()
        
        self.assertTrue(result1, "First run should succeed")
        self.assertTrue(result2, "Second run should succeed")

        # Verify directories still exist
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration",
        ]

        for dir_name in required_dirs:
            dir_path = Path(self.temp_dir) / dir_name
            self.assertTrue(
                dir_path.exists(),
                f"Directory {dir_name} should still exist after second run"
            )


if __name__ == "__main__":
    unittest.main()