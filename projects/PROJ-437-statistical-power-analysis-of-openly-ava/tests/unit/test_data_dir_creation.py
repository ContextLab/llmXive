"""
Unit tests for data directory creation functionality.

This test verifies that the create_data_directories function:
1. Creates the expected directory structure
2. Handles existing directories gracefully (idempotency)
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data_setup.create_data_dirs import create_data_directories


class TestDataDirectoryCreation:
    """Test cases for data directory creation."""
    
    def test_creates_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Call the function with our temporary base
            create_data_directories(base_path)
            
            # Verify the root data directory exists
            assert (base_path / "data").exists()
            assert (base_path / "data").is_dir()
            
            # Verify all subdirectories exist
            required_subdirs = ["raw", "derived", "aggregated"]
            for subdir in required_subdirs:
                subdir_path = base_path / "data" / subdir
                assert subdir_path.exists()
                assert subdir_path.is_dir()
    
    def test_idempotent(self):
        """Verify that running the function multiple times doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create directories first time
            create_data_directories(base_path)
            
            # Create directories second time - should not raise
            create_data_directories(base_path)
            
            # Verify structure is still correct
            assert (base_path / "data").exists()
            assert (base_path / "data" / "raw").exists()
            assert (base_path / "data" / "derived").exists()
            assert (base_path / "data" / "aggregated").exists()
    
    def test_creates_parent_directories(self):
        """Verify that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            # Ensure 'data' doesn't exist yet
            assert not (base_path / "data").exists()
            
            create_data_directories(base_path)
            
            assert (base_path / "data").exists()
            assert (base_path / "data" / "raw").exists()
    
    def test_empty_directories_created(self):
        """Verify that created directories are empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            create_data_directories(base_path)
            
            # Check that directories are empty (no files or subdirs)
            for subdir in ["raw", "derived", "aggregated"]:
                subdir_path = base_path / "data" / subdir
                assert len(list(subdir_path.iterdir())) == 0
