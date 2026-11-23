"""
Unit tests for the setup_data_dirs module.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest
from setup_data_dirs import create_directories, REQUIRED_DIRS


class TestCreateDirectories:
    def test_creates_all_required_dirs(self, tmp_path):
        """Test that all required directories are created."""
        created = create_directories(str(tmp_path))
        
        # Check count matches expected
        assert len(created) == len(REQUIRED_DIRS)
        
        # Check each required dir exists
        for dir_name in REQUIRED_DIRS:
            full_path = os.path.join(str(tmp_path), dir_name)
            assert os.path.exists(full_path), f"Directory {dir_name} was not created"
            assert os.path.isdir(full_path), f"{full_path} is not a directory"

    def test_idempotent_creation(self, tmp_path):
        """Test that running creation twice doesn't fail."""
        # First run
        created_first = create_directories(str(tmp_path))
        
        # Second run
        created_second = create_directories(str(tmp_path))
        
        # Both should succeed and return same count
        assert len(created_first) == len(created_second)
        
        # All dirs should still exist
        for dir_name in REQUIRED_DIRS:
            full_path = os.path.join(str(tmp_path), dir_name)
            assert os.path.exists(full_path)

    def test_nested_structure_created(self, tmp_path):
        """Test that nested directories (e.g., data/raw/synthetic_graphs) are created."""
        created = create_directories(str(tmp_path))
        
        # Check a specific nested path
        nested_path = os.path.join(str(tmp_path), "data", "raw", "synthetic_graphs")
        assert os.path.exists(nested_path), "Nested directory structure not created"
        
        processed_path = os.path.join(str(tmp_path), "data", "processed")
        assert os.path.exists(processed_path), "Processed data directory not created"