"""
Unit tests for the directory setup functionality.

Tests the ensure_directory and setup_project_structure functions
to ensure the required project structure is created correctly.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.setup_dirs import ensure_directory, setup_project_structure

class TestSetupDirs(unittest.TestCase):
    
    def setUp(self):
        """
        Create a temporary directory for testing.
        """
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """
        Clean up the temporary directory.
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_ensure_directory_creates_new_dir(self):
        """Test that ensure_directory creates a new directory."""
        new_dir = "test_new_dir"
        self.assertFalse(os.path.exists(new_dir))
        
        result = ensure_directory(new_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
        
    def test_ensure_directory_existing_dir(self):
        """Test that ensure_directory returns True for existing directory."""
        existing_dir = "test_existing_dir"
        os.makedirs(existing_dir, exist_ok=True)
        
        result = ensure_directory(existing_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(existing_dir))
        
    def test_ensure_directory_creates_parents(self):
        """Test that ensure_directory creates parent directories."""
        nested_dir = "parent/child/grandchild"
        self.assertFalse(os.path.exists(nested_dir))
        
        result = ensure_directory(nested_dir)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_dir))
        
    def test_setup_project_structure_creates_all_dirs(self):
        """Test that setup_project_structure creates all required directories."""
        result = setup_project_structure()
        
        self.assertTrue(result)
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "artifacts"
        ]
        
        for dir_name in required_dirs:
            full_path = os.path.join(self.test_dir, dir_name)
            self.assertTrue(os.path.exists(full_path), f"Directory {dir_name} was not created")
            self.assertTrue(os.path.isdir(full_path), f"{dir_name} is not a directory")

if __name__ == "__main__":
    unittest.main()