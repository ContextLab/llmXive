"""
Unit tests for the setup_structure.py script.
Verifies that the correct directory structure is created.
"""
import os
import shutil
import tempfile
import unittest
import sys

# Add the code directory to the path to import the script logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_structure import create_directories

class TestSetupStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a temporary directory to simulate the project root."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_cwd = os.getcwd()
        os.chdir(cls.temp_dir)

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary directory."""
        os.chdir(cls.original_cwd)
        shutil.rmtree(cls.temp_dir)

    def test_directory_creation(self):
        """Test that all required directories are created."""
        # Clear any existing structure first
        expected_dirs = [
            "code/data",
            "code/models",
            "code/utils",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-phase-change-predictive-power/contracts",
        ]

        # Run the creation logic
        create_directories()

        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = os.path.join(self.temp_dir, dir_path)
            self.assertTrue(
                os.path.isdir(full_path),
                f"Directory {dir_path} was not created."
            )

    def test_nested_directory_creation(self):
        """Test that nested directories are created correctly."""
        # The 'specs/001-phase-change-predictive-power/contracts' path is nested
        nested_path = os.path.join(self.temp_dir, "specs/001-phase-change-predictive-power/contracts")
        self.assertTrue(
            os.path.isdir(nested_path),
            "Nested directory structure was not created correctly."
        )

if __name__ == "__main__":
    unittest.main()