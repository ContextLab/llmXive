"""
Unit tests for hygiene.py utilities.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Adjust import path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.hygiene import compute_sha256, scan_directory


class TestComputeSha256:
    def test_compute_sha256_known_value(self, tmp_path):
        """Test SHA256 computation with known input."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA256 computation with empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)
        
        assert actual_hash == expected_hash


class TestScanDirectory:
    def test_scan_directory_single_file(self, tmp_path):
        """Test scanning a directory with a single file."""
        test_file = tmp_path / "file1.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        
        result = scan_directory(tmp_path)
        
        assert len(result) == 1
        assert "file1.txt" in result
        assert result["file1.txt"] == hashlib.sha256(content).hexdigest()
    
    def test_scan_directory_nested(self, tmp_path):
        """Test scanning a directory with nested subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        file1 = tmp_path / "file1.txt"
        file1.write_bytes(b"Content 1")
        
        file2 = subdir / "file2.txt"
        file2.write_bytes(b"Content 2")
        
        result = scan_directory(tmp_path)
        
        assert len(result) == 2
        assert "file1.txt" in result
        assert "subdir/file2.txt" in result
    
    def test_scan_directory_empty(self, tmp_path):
        """Test scanning an empty directory."""
        result = scan_directory(tmp_path)
        assert result == {}
    
    def test_scan_directory_nonexistent(self):
        """Test scanning a non-existent directory."""
        result = scan_directory(Path("/nonexistent/path"))
        assert result == {}
