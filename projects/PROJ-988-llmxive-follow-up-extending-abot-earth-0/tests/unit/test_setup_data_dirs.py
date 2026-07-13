"""
Unit tests for T004: Data directory structure setup.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Add code directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import create_directory_structure

class TestDataDirectorySetup(unittest.TestCase):
    """Tests for the data directory creation logic."""

    def setUp(self):
        """Create a temporary directory to act as the project root for testing."""
        self.test_root = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_root, "data")

    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root)

    def test_creates_top_level_directories(self):
        """Verify that raw, processed, results, and interim are created."""
        success = create_directory_structure(self.data_dir)
        
        self.assertTrue(success, "create_directory_structure should return True on success")
        
        required_dirs = ["raw", "processed", "results", "interim"]
        for subdir in required_dirs:
            dir_path = os.path.join(self.data_dir, subdir)
            self.assertTrue(os.path.isdir(dir_path), f"Directory {dir_path} should exist")

    def test_creates_nested_processed_directories(self):
        """Verify that specific nested processed directories are created."""
        success = create_directory_structure(self.data_dir)
        
        self.assertTrue(success)
        
        nested_dirs = [
            "processed/patches_100m2",
            "processed/degraded_base",
            "processed/nnf_varied_scenes",
            "processed/reconstructed/baseline",
            "processed/reconstructed/rendered_interface",
            "processed/reconstructed/inpainted"
        ]
        
        for subdir in nested_dirs:
            dir_path = os.path.join(self.data_dir, subdir)
            self.assertTrue(os.path.isdir(dir_path), f"Directory {dir_path} should exist")

    def test_idempotent_creation(self):
        """Verify that running the function twice does not cause errors."""
        success1 = create_directory_structure(self.data_dir)
        success2 = create_directory_structure(self.data_dir)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # Verify directories still exist
        self.assertTrue(os.path.isdir(os.path.join(self.data_dir, "raw")))

if __name__ == '__main__':
    unittest.main()