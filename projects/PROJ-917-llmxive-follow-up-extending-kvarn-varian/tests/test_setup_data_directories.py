"""
Unit tests for the setup_data_directories module.
"""
import os
import pytest
import tempfile
from pathlib import Path
import json
import sys

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from setup_data_directories import (
    get_project_root,
    create_directories,
    compute_file_checksum,
    record_checksums,
    save_checksums,
    load_checksums,
    verify_integrity
)


class TestDataDirectorySetup:
    """Test cases for data directory initialization."""

    def test_create_directories_structure(self, tmp_path):
        """Test that the required subdirectories are created."""
        # Create a temporary data root
        data_root = tmp_path / 'data'
        data_root.mkdir()
        
        # Mock the root_dir to be tmp_path
        created_dirs = create_directories(tmp_path)
        
        expected_subdirs = ['raw', 'processed', 'models', 'simulation']
        assert len(created_dirs) == len(expected_subdirs)
        
        for subdir in expected_subdirs:
            dir_path = data_root / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_compute_file_checksum_file(self, tmp_path):
        """Test checksum computation for a file."""
        file_path = tmp_path / 'test.txt'
        file_path.write_text("Hello, World!")
        
        checksum1 = compute_file_checksum(file_path)
        checksum2 = compute_file_checksum(file_path)
        
        assert len(checksum1) == 64  # SHA-256 hex length
        assert checksum1 == checksum2  # Deterministic

    def test_compute_file_checksum_directory(self, tmp_path):
        """Test checksum computation for a directory."""
        dir_path = tmp_path / 'test_dir'
        dir_path.mkdir()
        (dir_path / 'file1.txt').write_text("Content 1")
        (dir_path / 'file2.txt').write_text("Content 2")
        
        checksum1 = compute_file_checksum(dir_path)
        checksum2 = compute_file_checksum(dir_path)
        
        assert len(checksum1) == 64
        assert checksum1 == checksum2

    def test_record_and_save_checksums(self, tmp_path):
        """Test recording and saving checksums."""
        # Create directories
        created_dirs = create_directories(tmp_path)
        
        # Record checksums
        checksums = record_checksums(tmp_path, created_dirs)
        
        assert isinstance(checksums, dict)
        assert len(checksums) == 4  # raw, processed, models, simulation
        
        # Save to file
        output_path = tmp_path / 'checksums.json'
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            loaded = json.load(f)
        
        assert loaded == checksums

    def test_verify_integrity(self, tmp_path):
        """Test integrity verification."""
        # Create directories and record checksums
        created_dirs = create_directories(tmp_path)
        checksums = record_checksums(tmp_path, created_dirs)
        
        # Verification should pass
        assert verify_integrity(tmp_path, checksums) is True

    def test_verify_integrity_failure_missing_dir(self, tmp_path):
        """Test integrity verification fails on missing directory."""
        # Create directories
        created_dirs = create_directories(tmp_path)
        checksums = record_checksums(tmp_path, created_dirs)
        
        # Remove one directory
        (tmp_path / 'data' / 'raw').rmdir()
        
        # Verification should fail
        assert verify_integrity(tmp_path, checksums) is False

    def test_load_checksums_missing_file(self, tmp_path):
        """Test loading checksums from a non-existent file returns empty dict."""
        non_existent = tmp_path / 'non_existent.json'
        result = load_checksums(non_existent)
        assert result == {}
        assert isinstance(result, dict)
