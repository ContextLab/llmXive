"""
Unit tests for the download module.

These tests verify the download functionality without actually downloading data.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.download import (
    compute_sha256,
    ensure_directories,
    is_data_available,
    load_stored_checksum,
    save_checksum,
)


class TestComputeSha256:
    def test_compute_sha256_of_empty_file(self, tmp_path):
        """Test SHA-256 computation on an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.touch()
        
        checksum = compute_sha256(file_path)
        # SHA-256 of empty file is a known value
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected

    def test_compute_sha256_of_file_with_content(self, tmp_path):
        """Test SHA-256 computation on a file with known content."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")
        
        checksum = compute_sha256(file_path)
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected


class TestEnsureDirectories:
    def test_ensure_directories_creates_folders(self, tmp_path, monkeypatch):
        """Test that ensure_directories creates the required folders."""
        # Mock the PROJECT_ROOT to use tmp_path
        from src.data import download
        
        # Temporarily change the PROJECT_ROOT
        original_root = download.PROJECT_ROOT
        download.PROJECT_ROOT = tmp_path
        
        # Mock the subdirectories
        data_raw = tmp_path / "data" / "raw"
        cache_dir = tmp_path / "data" / "cache"
        state_dir = tmp_path / "state"
        
        try:
            ensure_directories()
            
            assert data_raw.exists()
            assert cache_dir.exists()
            assert state_dir.exists()
        finally:
            # Restore original value
            download.PROJECT_ROOT = original_root


class TestChecksumFunctions:
    def test_save_and_load_checksum(self, tmp_path, monkeypatch):
        """Test saving and loading a checksum."""
        from src.data import download
        
        # Mock the PROJECT_ROOT and CHECKSUM_FILE
        original_root = download.PROJECT_ROOT
        original_checksum_file = download.CHECKSUM_FILE
        
        test_checksum_file = tmp_path / "test_checksum.txt"
        download.CHECKSUM_FILE = test_checksum_file
        
        try:
            test_checksum = "abc123def456"
            save_checksum(test_checksum)
            
            assert test_checksum_file.exists()
            assert test_checksum_file.read_text().strip() == test_checksum
            
            loaded_checksum = load_stored_checksum()
            assert loaded_checksum == test_checksum
        finally:
            download.PROJECT_ROOT = original_root
            download.CHECKSUM_FILE = original_checksum_file

    def test_load_stored_checksum_when_file_not_exists(self, tmp_path, monkeypatch):
        """Test loading checksum when file doesn't exist."""
        from src.data import download
        
        original_checksum_file = download.CHECKSUM_FILE
        download.CHECKSUM_FILE = tmp_path / "nonexistent.txt"
        
        try:
            result = load_stored_checksum()
            assert result is None
        finally:
            download.CHECKSUM_FILE = original_checksum_file


class TestDataAvailability:
    def test_is_data_available_returns_false_when_empty(self, tmp_path, monkeypatch):
        """Test that is_data_available returns False when directory is empty."""
        from src.data import download
        
        original_root = download.PROJECT_ROOT
        original_data_raw = download.DATA_RAW_DIR
        
        download.PROJECT_ROOT = tmp_path
        download.DATA_RAW_DIR = tmp_path / "data" / "raw"
        
        try:
            # Create the directory but leave it empty
            download.DATA_RAW_DIR.mkdir(parents=True)
            
            result = is_data_available()
            assert result is False
        finally:
            download.PROJECT_ROOT = original_root
            download.DATA_RAW_DIR = original_data_raw

    def test_is_data_available_returns_true_when_not_empty(self, tmp_path, monkeypatch):
        """Test that is_data_available returns True when directory has content."""
        from src.data import download
        
        original_root = download.PROJECT_ROOT
        original_data_raw = download.DATA_RAW_DIR
        
        download.PROJECT_ROOT = tmp_path
        download.DATA_RAW_DIR = tmp_path / "data" / "raw"
        
        try:
            # Create the directory with a file
            download.DATA_RAW_DIR.mkdir(parents=True)
            (download.DATA_RAW_DIR / "test.txt").write_text("test")
            
            result = is_data_available()
            assert result is True
        finally:
            download.PROJECT_ROOT = original_root
            download.DATA_RAW_DIR = original_data_raw

    def test_is_data_available_returns_false_when_not_exists(self, tmp_path, monkeypatch):
        """Test that is_data_available returns False when directory doesn't exist."""
        from src.data import download
        
        original_root = download.PROJECT_ROOT
        original_data_raw = download.DATA_RAW_DIR
        
        download.PROJECT_ROOT = tmp_path
        download.DATA_RAW_DIR = tmp_path / "data" / "raw"
        
        try:
            # Don't create the directory
            result = is_data_available()
            assert result is False
        finally:
            download.PROJECT_ROOT = original_root
            download.DATA_RAW_DIR = original_data_raw
