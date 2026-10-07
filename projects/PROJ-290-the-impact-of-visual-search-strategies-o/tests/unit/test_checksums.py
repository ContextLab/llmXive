"""
Unit tests for the checksums module (code/data/checksums.py).
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Ensure we can import from the project root
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.checksums import (
    ensure_raw_directory,
    calculate_sha256,
    scan_and_hash_directory,
    save_checksums
)


class TestEnsureRawDirectory:
    def test_creates_directory_if_missing(self, tmp_path):
        """Test that ensure_raw_directory creates the directory if it doesn't exist."""
        test_dir = tmp_path / "new_raw_dir"
        assert not test_dir.exists()
        
        result = ensure_raw_directory(test_dir)
        
        assert result.exists()
        assert result.is_dir()

    def test_returns_existing_directory(self, tmp_path):
        """Test that ensure_raw_directory returns the path if it already exists."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        
        result = ensure_raw_directory(test_dir)
        
        assert result == test_dir
        assert result.exists()


class TestCalculateSha256:
    def test_correct_hash_for_known_file(self, tmp_path):
        """Test SHA256 calculation against a known string."""
        content = b"Hello, World!"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(file_path)
        
        assert actual_hash == expected_hash

    def test_empty_file(self, tmp_path):
        """Test SHA256 calculation for an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_sha256(file_path)
        
        assert actual_hash == expected_hash


class TestScanAndHashDirectory:
    def test_scans_single_file(self, tmp_path):
        """Test scanning a directory with a single file."""
        content = b"Test data"
        file_path = tmp_path / "data.txt"
        file_path.write_bytes(content)
        
        results = scan_and_hash_directory(tmp_path)
        
        assert len(results) == 1
        assert results[0]["file"] == "data.txt"
        assert results[0]["sha256"] == hashlib.sha256(content).hexdigest()
        assert "size_bytes" in results[0]

    def test_scans_nested_directories(self, tmp_path):
        """Test scanning a directory with nested subdirectories."""
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        
        content1 = b"File 1"
        content2 = b"File 2"
        
        (tmp_path / "file1.txt").write_bytes(content1)
        (sub_dir / "file2.txt").write_bytes(content2)
        
        results = scan_and_hash_directory(tmp_path)
        
        assert len(results) == 2
        files = [r["file"] for r in results]
        assert "file1.txt" in files
        assert "subdir/file2.txt" in files

    def test_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        results = scan_and_hash_directory(tmp_path)
        assert results == []


class TestSaveChecksums:
    def test_saves_valid_json(self, tmp_path):
        """Test that save_checksums creates a valid JSON file."""
        checksums = [
            {"file": "test.txt", "sha256": "abc123", "size_bytes": 100}
        ]
        output_path = tmp_path / "checksums.json"
        
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert "checksums" in data
        assert len(data["checksums"]) == 1
        assert data["checksums"][0]["file"] == "test.txt"