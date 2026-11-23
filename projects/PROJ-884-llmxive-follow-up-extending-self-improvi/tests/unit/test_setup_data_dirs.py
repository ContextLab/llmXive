import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.utils.setup_data_dirs import setup_data_directories, get_project_root

class TestSetupDataDirs:
    """Unit tests for data directory setup functionality."""

    def test_creates_required_hierarchy(self, tmp_path):
        """Test that the function creates data/raw and data/processed."""
        success, created = setup_data_directories(tmp_path, verbose=False)
        
        assert success is True
        assert len(created) == 3  # data, data/raw, data/processed
        
        data_root = tmp_path / "data"
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        
        assert data_root.exists()
        assert raw_dir.exists()
        assert processed_dir.exists()
        assert data_root.is_dir()
        assert raw_dir.is_dir()
        assert processed_dir.is_dir()

    def test_verifies_writability(self, tmp_path):
        """Test that the function verifies directories are writable."""
        success, created = setup_data_directories(tmp_path, verbose=False)
        
        assert success is True
        
        # Attempt to write a file to each directory
        for dir_path in [tmp_path / "data", tmp_path / "data" / "raw", tmp_path / "data" / "processed"]:
            test_file = dir_path / "test_write.txt"
            test_file.write_text("test")
            assert test_file.exists()
            assert test_file.read_text() == "test"
            test_file.unlink()

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles pre-existing directories gracefully."""
        # Pre-create the directories
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        (tmp_path / "data" / "processed").mkdir()
        
        success, created = setup_data_directories(tmp_path, verbose=False)
        
        # Should succeed even if they exist
        assert success is True
        # Should not report them as newly created
        assert len(created) == 0

    def test_get_project_root_fallback(self):
        """Test get_project_root fallback behavior."""
        # This test assumes we are running in a standard environment
        # where a marker might not be found immediately
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
    
    def test_idempotency(self, tmp_path):
        """Test that running the setup multiple times is safe."""
        # First run
        success1, created1 = setup_data_directories(tmp_path, verbose=False)
        assert success1 is True
        
        # Second run
        success2, created2 = setup_data_directories(tmp_path, verbose=False)
        assert success2 is True
        
        # Directories should still exist
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()