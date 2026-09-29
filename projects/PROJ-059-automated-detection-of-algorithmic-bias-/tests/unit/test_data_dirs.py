"""
Unit tests for the data directory creation functionality.

Tests verify that:
- The data directory structure is created correctly
- Existing directories are not modified
- The required subdirectories (raw, processed, validation) exist after execution
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from setup_data_dirs import create_data_directories


class TestDataDirectories:
    """Test suite for data directory creation."""

    def test_creates_all_required_directories(self):
        """Test that all required data subdirectories are created."""
        with tempfile.TemporaryDirectory() as temp_root:
            # Run the directory creation
            create_data_directories(temp_root)
            
            # Verify structure
            root = Path(temp_root)
            assert (root / "data").exists(), "data directory should exist"
            assert (root / "data" / "raw").exists(), "data/raw should exist"
            assert (root / "data" / "processed").exists(), "data/processed should exist"
            assert (root / "data" / "validation").exists(), "data/validation should exist"

    def test_handles_existing_directories(self):
        """Test that existing directories are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_root:
            # Pre-create one directory
            root = Path(temp_root)
            (root / "data" / "raw").mkdir(parents=True)
            
            # Run creation again - should not raise
            create_data_directories(temp_root)
            
            # Verify all still exist
            assert (root / "data" / "raw").exists()
            assert (root / "data" / "processed").exists()
            assert (root / "data" / "validation").exists()

    def test_creates_parent_directories(self):
        """Test that parent 'data' directory is created if missing."""
        with tempfile.TemporaryDirectory() as temp_root:
            # Ensure no data directory exists
            root = Path(temp_root)
            assert not (root / "data").exists()
            
            # Run creation
            create_data_directories(temp_root)
            
            # Verify parent and children exist
            assert (root / "data").exists()
            assert (root / "data" / "raw").exists()

    def test_is_directory(self):
        """Test that the created paths are directories, not files."""
        with tempfile.TemporaryDirectory() as temp_root:
            create_data_directories(temp_root)
            root = Path(temp_root)
            
            assert (root / "data").is_dir()
            assert (root / "data" / "raw").is_dir()
            assert (root / "data" / "processed").is_dir()
            assert (root / "data" / "validation").is_dir()