import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from t024c_checksum import compute_sha256_file, load_existing_checksums, save_checksums


class TestComputeSha256File:
    def test_compute_sha256_for_known_file(self, tmp_path):
        """Test checksum computation for a file with known content."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        # Compute checksum
        checksum = compute_sha256_file(test_file)
        
        # Expected SHA-256 for "Hello, World!"
        expected = "7f83b1657ff1fc53b92dc18148a1d65dfa5e7119c46636d6d2d7a54b0d2a5b7d"
        assert checksum == expected
    
    def test_compute_sha256_for_empty_file(self, tmp_path):
        """Test checksum computation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        checksum = compute_sha256_file(test_file)
        
        # Expected SHA-256 for empty content
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected
    
    def test_compute_sha256_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        non_existent = tmp_path / "non_existent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256_file(non_existent)


class TestLoadExistingChecksums:
    def test_load_existing_checksums_from_file(self, tmp_path):
        """Test loading checksums from an existing JSON file."""
        checksums_file = tmp_path / "checksums.json"
        data = {"files": {"test.npy": {"sha256": "abc123"}}}
        
        with open(checksums_file, "w") as f:
            json.dump(data, f)
        
        result = load_existing_checksums(checksums_file)
        assert result == data
    
    def test_load_existing_checksums_from_nonexistent_file(self, tmp_path):
        """Test loading checksums from a non-existent file returns empty dict."""
        non_existent = tmp_path / "non_existent.json"
        
        result = load_existing_checksums(non_existent)
        assert result == {"files": {}}


class TestSaveChecksums:
    def test_save_checksums_creates_file(self, tmp_path):
        """Test that save_checksums creates the file with correct content."""
        checksums_file = tmp_path / "checksums.json"
        data = {"files": {"test.npy": {"sha256": "abc123"}}}
        
        save_checksums(checksums_file, data)
        
        assert checksums_file.exists()
        
        with open(checksums_file, "r") as f:
            loaded = json.load(f)
        
        assert loaded == data
    
    def test_save_checksums_creates_directories(self, tmp_path):
        """Test that save_checksums creates parent directories if they don't exist."""
        nested_path = tmp_path / "subdir" / "checksums.json"
        data = {"files": {}}
        
        save_checksums(nested_path, data)
        
        assert nested_path.exists()