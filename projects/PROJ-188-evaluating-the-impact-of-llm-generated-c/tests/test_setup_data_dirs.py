import os
import shutil
from pathlib import Path
import tempfile
import pytest

from setup_data_dirs import create_data_directories

class TestDataDirectories:
    def test_creates_all_subdirectories(self, tmp_path):
        """Test that all required subdirectories are created."""
        data_root = tmp_path / "data"
        
        create_data_directories(str(data_root))
        
        assert (data_root / "raw").exists()
        assert (data_root / "intermediate").exists()
        assert (data_root / "processed").exists()
        
        # Verify they are directories
        assert (data_root / "raw").is_dir()
        assert (data_root / "intermediate").is_dir()
        assert (data_root / "processed").is_dir()

    def test_creates_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are created in each subdirectory."""
        data_root = tmp_path / "data"
        
        create_data_directories(str(data_root))
        
        for subdir in ["raw", "intermediate", "processed"]:
            gitkeep = data_root / subdir / ".gitkeep"
            assert gitkeep.exists()
            assert gitkeep.is_file()

    def test_idempotent_creation(self, tmp_path):
        """Test that running the function twice doesn't cause errors."""
        data_root = tmp_path / "data"
        
        # First run
        create_data_directories(str(data_root))
        
        # Second run should not raise
        create_data_directories(str(data_root))
        
        # Verify directories still exist
        assert (data_root / "raw").exists()
        assert (data_root / "intermediate").exists()
        assert (data_root / "processed").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        data_root = tmp_path / "deep" / "nested" / "data"
        
        create_data_directories(str(data_root))
        
        assert data_root.exists()
        assert (data_root / "raw").exists()
        assert (data_root / "intermediate").exists()
        assert (data_root / "processed").exists()