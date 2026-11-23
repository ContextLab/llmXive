"""
Unit tests for setup_data_dirs.py
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.setup_data_dirs import setup_data_directories


class TestSetupDataDirectories:
    """Tests for the setup_data_directories function."""

    def test_creates_raw_directory(self, tmp_path):
        """Test that the raw data directory is created."""
        result = setup_data_directories(tmp_path)
        
        assert "data_raw" in result
        assert Path(result["data_raw"]).exists()
        assert Path(result["data_raw"]).is_dir()

    def test_creates_processed_directory(self, tmp_path):
        """Test that the processed data directory is created."""
        result = setup_data_directories(tmp_path)
        
        assert "data_processed" in result
        assert Path(result["data_processed"]).exists()
        assert Path(result["data_processed"]).is_dir()

    def test_creates_gitkeep_in_raw(self, tmp_path):
        """Test that .gitkeep file is created in raw directory."""
        result = setup_data_directories(tmp_path)
        raw_dir = Path(result["data_raw"])
        
        assert (raw_dir / ".gitkeep").exists()
        assert (raw_dir / ".gitkeep").is_file()

    def test_creates_gitkeep_in_processed(self, tmp_path):
        """Test that .gitkeep file is created in processed directory."""
        result = setup_data_directories(tmp_path)
        processed_dir = Path(result["data_processed"])
        
        assert (processed_dir / ".gitkeep").exists()
        assert (processed_dir / ".gitkeep").is_file()

    def test_returns_correct_paths(self, tmp_path):
        """Test that the function returns correct directory paths."""
        result = setup_data_directories(tmp_path)
        
        expected_raw = tmp_path / "data" / "raw"
        expected_processed = tmp_path / "data" / "processed"
        
        assert result["data_raw"] == str(expected_raw)
        assert result["data_processed"] == str(expected_processed)

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles existing directories gracefully."""
        # Create directories beforehand
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        
        # Should not raise an exception
        result = setup_data_directories(tmp_path)
        
        assert "data_raw" in result
        assert "data_processed" in result

    def test_gitkeep_files_are_empty(self, tmp_path):
        """Test that .gitkeep files are empty (as expected for placeholders)."""
        result = setup_data_directories(tmp_path)
        
        raw_gitkeep = Path(result["data_raw"]) / ".gitkeep"
        processed_gitkeep = Path(result["data_processed"]) / ".gitkeep"
        
        assert raw_gitkeep.stat().st_size == 0
        assert processed_gitkeep.stat().st_size == 0