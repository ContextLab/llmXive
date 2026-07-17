import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import setup_data_directories
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_directories import setup_data_directories

class TestDataDirectories:
    def test_directories_created(self, tmp_path):
        """Test that the required data subdirectories are created."""
        setup_data_directories(tmp_path)
        
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        models_dir = data_dir / "models"
        
        assert data_dir.exists(), "data directory should be created"
        assert raw_dir.exists(), "data/raw directory should be created"
        assert processed_dir.exists(), "data/processed directory should be created"
        assert models_dir.exists(), "data/models directory should be created"
        
        assert data_dir.is_dir()
        assert raw_dir.is_dir()
        assert processed_dir.is_dir()
        assert models_dir.is_dir()

    def test_gitkeep_files_created(self, tmp_path):
        """Test that .gitkeep files are created in each directory."""
        setup_data_directories(tmp_path)
        
        data_dir = tmp_path / "data"
        gitkeep_files = [
            data_dir / ".gitkeep",
            data_dir / "raw" / ".gitkeep",
            data_dir / "processed" / ".gitkeep",
            data_dir / "models" / ".gitkeep"
        ]
        
        for gitkeep in gitkeep_files:
            assert gitkeep.exists(), f".gitkeep should exist at {gitkeep}"
            content = gitkeep.read_text()
            assert "llmXive" in content, ".gitkeep should contain project marker"

    def test_idempotent(self, tmp_path):
        """Test that running the setup twice doesn't cause errors."""
        # First run
        setup_data_directories(tmp_path)
        
        # Second run should not raise an exception
        setup_data_directories(tmp_path)
        
        # Verify directories still exist
        data_dir = tmp_path / "data"
        assert data_dir.exists()
        assert (data_dir / "raw").exists()
        assert (data_dir / "processed").exists()
        assert (data_dir / "models").exists()

    def test_nested_directory_creation(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        # Start with a clean tmp_path, no 'data' folder
        assert not (tmp_path / "data").exists()
        
        setup_data_directories(tmp_path)
        
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()