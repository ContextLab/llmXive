import os
import tempfile
from pathlib import Path
import pytest
from setup_data_dirs import create_data_directories


class TestDataDirectories:
    """Tests for data directory creation logic."""

    def test_creates_raw_directory(self, tmp_path):
        """Verify that the 'raw' subdirectory is created."""
        create_data_directories(tmp_path)
        raw_dir = tmp_path / "data" / "raw"
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_creates_processed_directory(self, tmp_path):
        """Verify that the 'processed' subdirectory is created."""
        create_data_directories(tmp_path)
        processed_dir = tmp_path / "data" / "processed"
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_creates_interim_directory(self, tmp_path):
        """Verify that the 'interim' subdirectory is created."""
        create_data_directories(tmp_path)
        interim_dir = tmp_path / "data" / "interim"
        assert interim_dir.exists()
        assert interim_dir.is_dir()

    def test_creates_gitkeep_files(self, tmp_path):
        """Verify that .gitkeep files are created in subdirectories."""
        create_data_directories(tmp_path)
        
        subdirs = ["raw", "processed", "interim"]
        for subdir in subdirs:
            gitkeep_path = tmp_path / "data" / subdir / ".gitkeep"
            assert gitkeep_path.exists()
            assert gitkeep_path.is_file()

    def test_idempotent_creation(self, tmp_path):
        """Verify that running the function twice does not cause errors."""
        create_data_directories(tmp_path)
        # Run again - should not raise
        create_data_directories(tmp_path)
        
        raw_dir = tmp_path / "data" / "raw"
        assert raw_dir.exists()