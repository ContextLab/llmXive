"""
Unit tests for the data directory setup functionality.

Verifies that the required directories are created correctly
and that the configuration module provides the expected paths.
"""
import os
import shutil
import tempfile
from pathlib import Path
import sys
import pytest

# Add parent directory to path to allow importing config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    DATA_DIR,
    RAW_DATA_DIR,
    SYNTHETIC_DATA_DIR,
    PROCESSED_DATA_DIR,
    ensure_directories,
    get_data_path
)

class TestDataDirectorySetup:
    """Tests for data directory creation and path utilities."""

    def test_ensure_directories_creates_all_dirs(self, tmp_path):
        """Test that ensure_directories creates all required directories."""
        # Mock the global paths to use a temporary directory
        original_data_dir = DATA_DIR
        original_raw_dir = RAW_DATA_DIR
        original_synthetic_dir = SYNTHETIC_DATA_DIR
        original_processed_dir = PROCESSED_DATA_DIR

        try:
            # Set up temporary paths
            temp_data = tmp_path / "data"
            temp_raw = temp_data / "raw"
            temp_synthetic = temp_data / "synthetic"
            temp_processed = temp_data / "processed"

            # Temporarily override the module-level variables
            import config
            config.DATA_DIR = temp_data
            config.RAW_DATA_DIR = temp_raw
            config.SYNTHETIC_DATA_DIR = temp_synthetic
            config.PROCESSED_DATA_DIR = temp_processed

            # Call the function
            result = ensure_directories()

            # Assert success
            assert result is True
            assert temp_data.exists()
            assert temp_raw.exists()
            assert temp_synthetic.exists()
            assert temp_processed.exists()

        finally:
            # Restore original paths
            config.DATA_DIR = original_data_dir
            config.RAW_DATA_DIR = original_raw_dir
            config.SYNTHETIC_DATA_DIR = original_synthetic_dir
            config.PROCESSED_DATA_DIR = original_processed_dir

    def test_ensure_directories_idempotent(self, tmp_path):
        """Test that calling ensure_directories multiple times doesn't cause errors."""
        # Mock the global paths
        import config
        original_data_dir = config.DATA_DIR
        original_raw_dir = config.RAW_DATA_DIR
        original_synthetic_dir = config.SYNTHETIC_DATA_DIR
        original_processed_dir = config.PROCESSED_DATA_DIR

        try:
            temp_data = tmp_path / "data"
            temp_raw = temp_data / "raw"
            temp_synthetic = temp_data / "synthetic"
            temp_processed = temp_data / "processed"

            config.DATA_DIR = temp_data
            config.RAW_DATA_DIR = temp_raw
            config.SYNTHETIC_DATA_DIR = temp_synthetic
            config.PROCESSED_DATA_DIR = temp_processed

            # Call twice
            result1 = ensure_directories()
            result2 = ensure_directories()

            assert result1 is True
            assert result2 is True

        finally:
            config.DATA_DIR = original_data_dir
            config.RAW_DATA_DIR = original_raw_dir
            config.SYNTHETIC_DATA_DIR = original_synthetic_dir
            config.PROCESSED_DATA_DIR = original_processed_dir

    def test_get_data_path_valid_subdirs(self):
        """Test get_data_path with valid subdirectories."""
        # Test 'raw'
        path = get_data_path("raw", "test.json")
        assert path == RAW_DATA_DIR / "test.json"

        # Test 'synthetic'
        path = get_data_path("synthetic", "image.png")
        assert path == SYNTHETIC_DATA_DIR / "image.png"

        # Test 'processed'
        path = get_data_path("processed", "results.csv")
        assert path == PROCESSED_DATA_DIR / "results.csv"

    def test_get_data_path_invalid_subdir(self):
        """Test get_data_path raises ValueError for invalid subdirectory."""
        with pytest.raises(ValueError, match="Invalid subdirectory"):
            get_data_path("invalid", "file.txt")

    def test_directory_structure_exists_after_setup(self, tmp_path):
        """Integration test: verify directory structure after running setup."""
        import config
        original_data_dir = config.DATA_DIR
        original_raw_dir = config.RAW_DATA_DIR
        original_synthetic_dir = config.SYNTHETIC_DATA_DIR
        original_processed_dir = config.PROCESSED_DATA_DIR

        try:
            temp_data = tmp_path / "data"
            config.DATA_DIR = temp_data
            config.RAW_DATA_DIR = temp_data / "raw"
            config.SYNTHETIC_DATA_DIR = temp_data / "synthetic"
            config.PROCESSED_DATA_DIR = temp_data / "processed"

            ensure_directories()

            assert temp_data.is_dir()
            assert (temp_data / "raw").is_dir()
            assert (temp_data / "synthetic").is_dir()
            assert (temp_data / "processed").is_dir()

        finally:
            config.DATA_DIR = original_data_dir
            config.RAW_DATA_DIR = original_raw_dir
            config.SYNTHETIC_DATA_DIR = original_synthetic_dir
            config.PROCESSED_DATA_DIR = original_processed_dir
