"""
Unit tests for the setup_directories module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.setup_directories import create_directories

class TestCreateDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that the function creates data/raw and data/processed."""
        result = create_directories(tmp_path)
        
        assert result is True
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "raw").is_dir()
        assert (tmp_path / "data" / "processed").is_dir()

    def test_idempotent_on_existing(self, tmp_path):
        """Test that running the function twice does not raise errors."""
        # Create directories manually first
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        
        result = create_directories(tmp_path)
        
        assert result is True
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if missing."""
        # Ensure 'data' does not exist
        data_dir = tmp_path / "data"
        assert not data_dir.exists()
        
        result = create_directories(tmp_path)
        
        assert result is True
        assert data_dir.exists()
        assert (data_dir / "raw").exists()
        assert (data_dir / "processed").exists()