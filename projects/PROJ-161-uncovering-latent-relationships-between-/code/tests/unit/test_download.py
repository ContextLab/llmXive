"""
Unit tests for data download module.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.data.download import calculate_sha256, verify_checksum, log_data_version
from src.data.schema import load_data_version_from_file

class TestChecksumCalculation:
    """Tests for checksum calculation functions."""
    
    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation on a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(test_file)
        
        # Known SHA256 for "Hello, World!"
        expected_checksum = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected_checksum
    
    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA256 calculation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        checksum = calculate_sha256(test_file)
        
        # Known SHA256 for empty string
        expected_checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected_checksum
    
    def test_verify_checksum_match(self, tmp_path):
        """Test checksum verification when values match."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)
        
        checksum = calculate_sha256(test_file)
        assert verify_checksum(test_file, checksum) is True
    
    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum verification when values don't match."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        # Wrong checksum
        assert verify_checksum(test_file, "wrong_checksum") is False

class TestDataVersionLogging:
    """Tests for data version logging functionality."""
    
    def test_log_data_version_creates_file(self, tmp_path):
        """Test that log_data_version creates the data_version.json file."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        data_version_path = tmp_path / "data_version.json"
        
        log_data_version("http://example.com/test", test_file, data_version_path)
        
        assert data_version_path.exists()
        
        # Verify file contents
        with open(data_version_path) as f:
            data_version = json.load(f)
        
        assert "files" in data_version
        assert len(data_version["files"]) == 1
        
        entry = data_version["files"][0]
        assert entry["source_url"] == "http://example.com/test"
        assert "checksum_sha256" in entry
        assert "timestamp" in entry
    
    def test_log_data_version_updates_existing(self, tmp_path):
        """Test that log_data_version updates existing entries."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        data_version_path = tmp_path / "data_version.json"
        
        # Log first entry
        log_data_version("http://example.com/test1", test_file, data_version_path)
        
        # Log second entry with different URL
        log_data_version("http://example.com/test2", test_file, data_version_path)
        
        with open(data_version_path) as f:
            data_version = json.load(f)
        
        assert len(data_version["files"]) == 2
        
        # Verify both entries exist
        urls = [entry["source_url"] for entry in data_version["files"]]
        assert "http://example.com/test1" in urls
        assert "http://example.com/test2" in urls
    
    def test_log_data_version_updates_same_url(self, tmp_path):
        """Test that log_data_version updates existing entries with same URL."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        data_version_path = tmp_path / "data_version.json"
        
        # Log first entry
        log_data_version("http://example.com/test", test_file, data_version_path)
        
        # Log same URL again (should update)
        log_data_version("http://example.com/test", test_file, data_version_path)
        
        with open(data_version_path) as f:
            data_version = json.load(f)
        
        assert len(data_version["files"]) == 1
        
        entry = data_version["files"][0]
        assert entry["source_url"] == "http://example.com/test"
    
    def test_log_data_version_timestamp_format(self, tmp_path):
        """Test that timestamp is in ISO format."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        data_version_path = tmp_path / "data_version.json"
        
        log_data_version("http://example.com/test", test_file, data_version_path)
        
        with open(data_version_path) as f:
            data_version = json.load(f)
        
        timestamp = data_version["files"][0]["timestamp"]
        
        # Should be valid ISO format (no exception raised)
        from datetime import datetime
        datetime.fromisoformat(timestamp)
    
    def test_log_data_version_checksum_match(self, tmp_path):
        """Test that logged checksum matches actual file checksum."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content for checksum verification"
        test_file.write_bytes(test_content)
        
        data_version_path = tmp_path / "data_version.json"
        
        log_data_version("http://example.com/test", test_file, data_version_path)
        
        with open(data_version_path) as f:
            data_version = json.load(f)
        
        logged_checksum = data_version["files"][0]["checksum_sha256"]
        actual_checksum = calculate_sha256(test_file)
        
        assert logged_checksum == actual_checksum
