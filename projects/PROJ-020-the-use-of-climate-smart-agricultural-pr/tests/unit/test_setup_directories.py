"""
Unit tests for the directory setup functionality.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.setup_directories import setup_directories

class TestSetupDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that setup_directories creates the required structure."""
        # Call the function
        setup_directories(tmp_path)
        
        # Verify directories exist
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "state").exists()
    
    def test_creates_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are created in each directory."""
        setup_directories(tmp_path)
        
        # Verify .gitkeep files exist
        assert (tmp_path / "data" / "raw" / ".gitkeep").exists()
        assert (tmp_path / "data" / "processed" / ".gitkeep").exists()
        assert (tmp_path / "state" / ".gitkeep").exists()
    
    def test_idempotent(self, tmp_path):
        """Test that running setup twice does not cause errors."""
        # Run twice
        setup_directories(tmp_path)
        setup_directories(tmp_path)
        
        # Verify directories still exist
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "state").exists()
    
    def test_nested_structure(self, tmp_path):
        """Test that parent directories are created if missing."""
        # Remove data directory to test parent creation
        data_dir = tmp_path / "data"
        if data_dir.exists():
            data_dir.rmdir()
        
        setup_directories(tmp_path)
        
        # Verify full structure exists
        assert data_dir.exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "state").exists()