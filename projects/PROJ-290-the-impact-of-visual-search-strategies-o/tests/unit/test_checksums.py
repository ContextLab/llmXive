"""
Unit tests for T015: checksums.py
Tests directory creation and hash calculation logic.
"""
import os
import json
import tempfile
import shutil
import hashlib
from pathlib import Path
import pytest

# We will mock config to avoid needing a full project state for unit tests
# but we test the core logic functions directly if possible, or via the main flow with mocks.

# Import the functions we want to test
# Note: We are testing the logic inside code/data/checksums.py
# Since that file imports from config and utils, we need to be careful.
# We will test the helper logic by importing the module and mocking dependencies if necessary.
# However, for T015, the logic is straightforward: ensure dir, scan, hash, save.

from code.data.checksums import ensure_raw_directory, scan_and_hash_directory, save_checksums


class TestEnsureRawDirectory:
    def test_creates_directory(self, tmp_path):
        """Test that the function creates the directory if it doesn't exist."""
        # Simulate a config object
        class MockConfig:
            def get(self, key, default=None):
                if key == "paths":
                    return {"data_raw": str(tmp_path / "raw")}
                return default

        config = MockConfig()
        result_path = ensure_raw_directory(config)
        
        assert result_path.exists()
        assert result_path.is_dir()
        assert result_path.name == "raw"

    def test_uses_existing_directory(self, tmp_path):
        """Test that the function uses the directory if it already exists."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        class MockConfig:
            def get(self, key, default=None):
                if key == "paths":
                    return {"data_raw": str(raw_dir)}
                return default

        config = MockConfig()
        result_path = ensure_raw_directory(config)
        
        assert result_path == raw_dir
        assert result_path.exists()


class TestScanAndHashDirectory:
    def test_hashes_single_file(self, tmp_path):
        """Test hashing a single file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        results = scan_and_hash_directory(tmp_path)
        
        assert len(results) == 1
        assert results[0]["relative_path"] == "test.txt"
        assert results[0]["sha256"] == expected_hash
        assert results[0]["size_bytes"] == len(content)

    def test_handles_nested_directories(self, tmp_path):
        """Test hashing files in nested directories."""
        nested_dir = tmp_path / "sub"
        nested_dir.mkdir()
        file1 = tmp_path / "file1.txt"
        file2 = nested_dir / "file2.txt"
        
        file1.write_bytes(b"data1")
        file2.write_bytes(b"data2")
        
        results = scan_and_hash_directory(tmp_path)
        
        assert len(results) == 2
        paths = {r["relative_path"] for r in results}
        assert "file1.txt" in paths
        assert "sub/file2.txt" in paths

    def test_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        results = scan_and_hash_directory(tmp_path)
        assert len(results) == 0

    def test_non_existent_directory(self, tmp_path):
        """Test scanning a directory that doesn't exist."""
        non_existent = tmp_path / "does_not_exist"
        results = scan_and_hash_directory(non_existent)
        assert len(results) == 0


class TestSaveChecksums:
    def test_saves_json_correctly(self, tmp_path):
        """Test that checksums are saved to a valid JSON file."""
        output_file = tmp_path / "checksums.json"
        test_data = [
            {"relative_path": "a.txt", "sha256": "abc123", "size_bytes": 10}
        ]
        
        save_checksums(test_data, output_file)
        
        assert output_file.exists()
        with open(output_file, "r") as f:
            data = json.load(f)
        
        assert "checksums" in data
        assert len(data["checksums"]) == 1
        assert data["checksums"][0]["relative_path"] == "a.txt"
        assert data["checksums"][0]["sha256"] == "abc123"