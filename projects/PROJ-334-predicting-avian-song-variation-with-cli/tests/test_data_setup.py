"""
Tests for data directory setup functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
import code.data_setup as data_setup_module


class TestDataSetup:
    """Test cases for data directory setup."""

    def test_ensure_directory_creates_new_dir(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        
        # Patch the function to work with our temp directory
        with patch.object(data_setup_module, 'DATA_DIR', tmp_path):
            data_setup_module.ensure_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists(self, tmp_path):
        """Test that ensure_directory handles existing directories."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        with patch.object(data_setup_module, 'DATA_DIR', tmp_path):
            # Should not raise an error
            data_setup_module.ensure_directory(existing_dir)
        
        assert existing_dir.exists()

    def test_initialize_checksums_file_creates_new(self, tmp_path):
        """Test that initialize_checksums_file creates a new file with header."""
        checksums_file = tmp_path / "checksums.txt"
        
        with patch.object(data_setup_module, 'CHECKSUMS_FILE', checksums_file):
            data_setup_module.initialize_checksums_file()
        
        assert checksums_file.exists()
        content = checksums_file.read_text()
        assert "# Data Artifact Checksums" in content
        assert "sha256_hash" in content
        assert "relative_path" in content

    def test_initialize_checksums_file_exists(self, tmp_path):
        """Test that initialize_checksums_file handles existing file."""
        checksums_file = tmp_path / "checksums.txt"
        checksums_file.write_text("existing content\n")
        
        with patch.object(data_setup_module, 'CHECKSUMS_FILE', checksums_file):
            # Should not raise an error
            data_setup_module.initialize_checksums_file()
        
        # Content should remain unchanged
        assert checksums_file.read_text() == "existing content\n"

    def test_main_executes_successfully(self, tmp_path):
        """Test that main() runs without errors and creates expected structure."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        checksums_file = data_dir / "checksums.txt"
        
        with patch.object(data_setup_module, 'DATA_DIR', data_dir):
            with patch.object(data_setup_module, 'RAW_DIR', raw_dir):
                with patch.object(data_setup_module, 'PROCESSED_DIR', processed_dir):
                    with patch.object(data_setup_module, 'CHECKSUMS_FILE', checksums_file):
                        data_setup_module.main()
        
        # Verify directories were created
        assert data_dir.exists()
        assert raw_dir.exists()
        assert processed_dir.exists()
        
        # Verify checksums file was created
        assert checksums_file.exists()
        content = checksums_file.read_text()
        assert "# Data Artifact Checksums" in content

    def test_path_structure_correct(self, tmp_path):
        """Test that the directory structure follows the expected pattern."""
        data_dir = tmp_path / "data"
        
        with patch.object(data_setup_module, 'DATA_DIR', data_dir):
            data_setup_module.main()
        
        # Check that raw and processed are subdirectories of data
        assert (data_dir / "raw").exists()
        assert (data_dir / "processed").exists()
        assert (data_dir / "checksums.txt").exists()
