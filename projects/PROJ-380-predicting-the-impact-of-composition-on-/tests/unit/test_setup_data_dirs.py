import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_structure

class TestDataDirectorySetup:
    """Tests for the data directory structure setup functionality."""

    def test_creates_data_root_if_missing(self, tmp_path):
        """Test that the data root directory is created if it doesn't exist."""
        data_root = tmp_path / "data"
        
        result = setup_data_structure(base_dir=tmp_path)
        
        assert result is True
        assert data_root.exists()
        assert data_root.is_dir()

    def test_creates_all_subdirectories(self, tmp_path):
        """Test that raw, processed, and artifacts subdirectories are created."""
        result = setup_data_structure(base_dir=tmp_path)
        
        assert result is True
        
        data_root = tmp_path / "data"
        sub_dirs = ["raw", "processed", "artifacts"]
        
        for sub_dir in sub_dirs:
            target_path = data_root / sub_dir
            assert target_path.exists()
            assert target_path.is_dir()

    def test_idempotent_when_directories_exist(self, tmp_path):
        """Test that the function handles existing directories gracefully."""
        # Pre-create the structure
        data_root = tmp_path / "data"
        data_root.mkdir()
        (data_root / "raw").mkdir()
        (data_root / "processed").mkdir()
        (data_root / "artifacts").mkdir()
        
        # Run setup again
        result = setup_data_structure(base_dir=tmp_path)
        
        assert result is True
        # All directories should still exist
        assert (data_root / "raw").exists()
        assert (data_root / "processed").exists()
        assert (data_root / "artifacts").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if necessary."""
        # Create a nested structure where data is deep
        nested_base = tmp_path / "project" / "src"
        
        result = setup_data_structure(base_dir=nested_base)
        
        assert result is True
        assert (nested_base / "data").exists()
        assert (nested_base / "data" / "raw").exists()
        assert (nested_base / "data" / "processed").exists()
        assert (nested_base / "data" / "artifacts").exists()
