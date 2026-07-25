"""
Unit tests for the setup_directories module (Task T001).
"""
import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """
        Create a temporary directory to act as the project root for testing.
        """
        self.test_root = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.test_root)

    def tearDown(self):
        """
        Clean up the temporary directory and restore original working directory.
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_create_directories_structure(self):
        """
        Test that create_directories creates all required directories.
        """
        # Run the setup
        success = create_directories()
        
        self.assertTrue(success, "create_directories should return True on success")
        
        # Verify each directory exists
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts",
        ]
        
        for dir_path in required_dirs:
            full_path = self.test_root / dir_path
            self.assertTrue(full_path.exists(), f"Directory {full_path} should exist")
            self.assertTrue(full_path.is_dir(), f"{full_path} should be a directory")

    def test_create_directories_idempotency(self):
        """
        Test that running create_directories multiple times doesn't fail.
        """
        # Run twice
        first_run = create_directories()
        second_run = create_directories()
        
        self.assertTrue(first_run)
        self.assertTrue(second_run)

    def test_nested_directories_created(self):
        """
        Test that nested directories (like specs/.../contracts) are created with parents.
        """
        success = create_directories()
        self.assertTrue(success)
        
        # Check the deepest nested path
        nested_path = self.test_root / "specs/001-investigating-the-correlation-between-gu/contracts"
        self.assertTrue(nested_path.exists())
        self.assertTrue(nested_path.is_dir())

if __name__ == "__main__":
    unittest.main()
