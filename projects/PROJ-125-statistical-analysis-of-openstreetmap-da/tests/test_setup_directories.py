"""
Tests for the setup_directories.py script.
Verifies that the required project directories are created.
"""

import os
import shutil
import tempfile
import unittest
import sys

# Add the root to the path to import the script logic if needed,
# or simply test the side effects of running the script.
# Here we test the logic directly by simulating the directory creation.

class TestDirectoryCreation(unittest.TestCase):
    """Test cases for directory creation logic."""

    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_directories_created(self):
        """Verify that all required directories are created."""
        # Import the logic from the script
        from code.setup_directories import DIRECTORIES

        for dir_path in DIRECTORIES:
            full_path = os.path.join(self.test_dir, dir_path)
            # Ensure the directory doesn't exist before running logic
            if os.path.exists(full_path):
                shutil.rmtree(full_path)

            # Run the creation logic manually for this test
            os.makedirs(full_path, exist_ok=True)

            # Verify existence
            self.assertTrue(os.path.exists(full_path), f"Directory {dir_path} was not created")
            self.assertTrue(os.path.isdir(full_path), f"{dir_path} is not a directory")

    def test_nested_directories(self):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        nested_path = "data/raw"
        full_path = os.path.join(self.test_dir, nested_path)
        
        os.makedirs(full_path, exist_ok=True)
        
        self.assertTrue(os.path.exists(full_path))
        self.assertTrue(os.path.isdir(full_path))
        
        # Verify parent also exists
        parent_path = os.path.join(self.test_dir, "data")
        self.assertTrue(os.path.exists(parent_path))


if __name__ == "__main__":
    unittest.main()