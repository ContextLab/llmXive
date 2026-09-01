"""
Unit tests for the directory setup script.
Verifies that the expected directory structure is created.
"""
import unittest
import os
from pathlib import Path
import tempfile
import shutil
import sys

# Add the project root to the path to allow imports
# Assuming this test file is at code/tests/test_setup_directories.py
# and the script is at code/setup_directories.py
# We need to go up two levels to reach the project root
current_dir = Path(__file__).resolve()
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_directories import create_directories, DIRECTORIES

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        # Change to the temp directory to simulate the project root
        os.chdir(self.temp_dir)
        
        # We need to reload the module to pick up the new cwd if it relied on __file__
        # However, our script uses Path(__file__).resolve().parent.parent
        # which is fixed relative to the script location, not cwd.
        # To test effectively, we will mock the ROOT_DIR logic or adjust the test.
        # Since the script hardcodes ROOT_DIR based on its own location, 
        # we will test the logic of directory creation by importing the function 
        # and verifying it creates dirs relative to where the script thinks the root is.
        # For this test, we will assume the script is run from the project root context
        # or we adjust the test to verify the *names* are correct.
        
        # Better approach: Test the list of directories and the creation logic directly
        # by patching the ROOT_DIR in the module.
        import code.setup_directories as sd
        self.original_root = sd.ROOT_DIR
        sd.ROOT_DIR = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Restore original ROOT_DIR
        import code.setup_directories as sd
        sd.ROOT_DIR = self.original_root

    def test_creates_all_directories(self):
        """Test that all required directories are created."""
        # Run the creation logic
        create_directories()
        
        # Verify each directory exists
        for dir_name in DIRECTORIES:
            target_path = Path(self.temp_dir) / dir_name
            self.assertTrue(target_path.exists(), f"Directory {dir_name} was not created.")
            self.assertTrue(target_path.is_dir(), f"{dir_name} exists but is not a directory.")

    def test_nested_directories_created(self):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        create_directories()
        
        # Check specific nested paths
        nested_dirs = ["data/raw", "data/processed", "data/results", "data/research"]
        for dir_name in nested_dirs:
            target_path = Path(self.temp_dir) / dir_name
            self.assertTrue(target_path.exists(), f"Nested directory {dir_name} was not created.")

    def test_idempotency(self):
        """Test that running the script twice does not cause errors."""
        # First run
        create_directories()
        # Second run
        count = create_directories()
        # Should report 0 new directories created
        self.assertEqual(count, 0, "Second run should not create new directories.")

if __name__ == "__main__":
    unittest.main()
