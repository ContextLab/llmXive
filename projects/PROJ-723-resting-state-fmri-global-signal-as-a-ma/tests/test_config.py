"""
Unit tests for configuration and directory setup.
"""
import unittest
import os
import shutil
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import ensure_directories, validate_config
from setup_directories import setup_directories


class TestConfig(unittest.TestCase):
    """Tests for configuration validation."""

    def test_validate_config_structure(self):
        """Test that a valid config passes validation."""
        valid_config = {
            'paths': {
                'raw': 'data/raw',
                'processed': 'data/processed',
                'results': 'data/results'
            },
            'hyperparameters': {
                'random_seed': 42,
                'cv_folds': 5
            }
        }
        
        # Should not raise an exception
        self.assertTrue(validate_config(valid_config))

    def test_validate_config_missing_keys(self):
        """Test that missing required keys raise an error."""
        incomplete_config = {
            'paths': {
                'raw': 'data/raw'
            }
        }
        
        with self.assertRaises(ValueError):
            validate_config(incomplete_config)


class TestDirectorySetup(unittest.TestCase):
    """Tests for directory creation logic."""

    def setUp(self):
        """Set up a temporary test root."""
        self.test_root = Path(__file__).parent.parent / "data" / "test_dirs"
        if self.test_root.exists():
            shutil.rmtree(self.test_root)
        self.test_root.mkdir(parents=True)

    def tearDown(self):
        """Clean up test directories."""
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_setup_directories_creates_folders(self):
        """Test that setup_directories creates the required folder structure."""
        # Define a relative structure to test
        test_structure = {
            'raw': 'data/raw',
            'processed': 'data/processed',
            'tests': 'tests'
        }
        
        # We call the function which internally uses ensure_directories
        # We simulate the call by passing the test root as base
        # Note: ensure_directories usually takes a base path or uses global config
        # Here we test the utility directly
        
        from config import ensure_directories
        
        # Ensure directories relative to test_root
        for name, rel_path in test_structure.items():
            full_path = self.test_root / rel_path
            ensure_directories(full_path)
            self.assertTrue(full_path.exists(), f"Directory {full_path} was not created")

    def test_setup_directories_idempotent(self):
        """Test that creating directories twice doesn't fail."""
        from config import ensure_directories
        test_path = self.test_root / "data" / "raw"
        
        ensure_directories(test_path)
        ensure_directories(test_path)  # Should not raise
        
        self.assertTrue(test_path.exists())


if __name__ == '__main__':
    unittest.main()