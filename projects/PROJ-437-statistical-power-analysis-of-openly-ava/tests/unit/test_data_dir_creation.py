"""
Unit tests for data directory creation functionality.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_setup.create_data_dirs import create_data_directories

class TestDataDirectoryCreation:
    """Tests for the create_data_directories function."""

    def test_creates_required_directories(self, tmp_path):
        """Test that all required data directories are created."""
        # Call the function
        create_data_directories(tmp_path)

        # Verify directories exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "aggregated").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        # Start with an empty temp directory
        assert not (tmp_path / "data").exists()
        
        create_data_directories(tmp_path)
        
        # Verify all directories were created
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "aggregated").exists()

    def test_idempotent_creation(self, tmp_path):
        """Test that calling the function multiple times doesn't cause errors."""
        # First call
        create_data_directories(tmp_path)
        
        # Second call should not raise an error
        create_data_directories(tmp_path)
        
        # Verify directories still exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "aggregated").exists()

    def test_directory_structure_is_valid(self, tmp_path):
        """Test that the created directories have the correct structure."""
        create_data_directories(tmp_path)
        
        data_dir = tmp_path / "data"
        
        # Check that it's a directory
        assert data_dir.is_dir()
        
        # Check that subdirectories exist and are directories
        for subdir in ["raw", "derived", "aggregated"]:
            subdir_path = data_dir / subdir
            assert subdir_path.is_dir()
            assert subdir_path in data_dir.iterdir()
