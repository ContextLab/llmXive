"""
Unit tests for the checksums module.

Tests cover:
- Single file SHA256 calculation
- Directory scanning and checksumming
- JSON serialization and deserialization
- Verification logic
- Error handling
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.checksums import (
    calculate_file_sha256,
    calculate_directory_checksums,
    save_checksums_to_json,
    load_checksums_from_json,
    verify_checksums,
    generate_raw_data_checksums
)


class TestCalculateFileSha256:
    """Tests for single file SHA256 calculation."""

    def test_calculate_hash_simple_string(self, tmp_path):
        """Test hashing a simple text file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_sha256(test_file)

        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA256 hex length

    def test_calculate_hash_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = calculate_file_sha256(test_file)

        assert actual_hash == expected_hash

    def test_calculate_hash_binary_file(self, tmp_path):
        """Test hashing a binary file with non-text bytes."""
        test_file = tmp_path / "binary.bin"
        content = bytes([0x00, 0xFF, 0x12, 0x34, 0xAB, 0xCD])
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_file_sha256(test_file)

        assert actual_hash == expected_hash

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            calculate_file_sha256(non_existent)

    def test_path_is_directory(self, tmp_path):
        """Test that ValueError is raised if path is a directory."""
        with pytest.raises(ValueError):
            calculate_file_sha256(tmp_path)


class TestCalculateDirectoryChecksums:
    """Tests for directory checksumming."""

    def test_scan_single_file(self, tmp_path):
        """Test scanning a directory with a single file."""
        test_file = tmp_path / "data.csv"
        test_file.write_text("col1,col2\n1,2\n")

        checksums = calculate_directory_checksums(tmp_path)

        assert len(checksums) == 1
        assert "data.csv" in checksums
        assert len(checksums["data.csv"]) == 64

    def test_scan_multiple_files(self, tmp_path):
        """Test scanning a directory with multiple files."""
        (tmp_path / "file1.csv").write_text("data1")
        (tmp_path / "file2.json").write_text("{}")
        (tmp_path / "file3.txt").write_text("text")

        checksums = calculate_directory_checksums(tmp_path)

        assert len(checksums) == 3
        assert "file1.csv" in checksums
        assert "file2.json" in checksums
        assert "file3.txt" in checksums

    def test_filter_by_extension(self, tmp_path):
        """Test filtering files by extension."""
        (tmp_path / "data.csv").write_text("data")
        (tmp_path / "readme.md").write_text("readme")
        (tmp_path / "script.py").write_text("code")

        checksums = calculate_directory_checksums(tmp_path, extensions=[".csv"])

        assert len(checksums) == 1
        assert "data.csv" in checksums
        assert "readme.md" not in checksums

    def test_recursive_scan(self, tmp_path):
        """Test recursive scanning of subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        (tmp_path / "root.csv").write_text("root")
        (subdir / "nested.csv").write_text("nested")

        checksums = calculate_directory_checksums(tmp_path, recursive=True)

        assert len(checksums) == 2
        assert "root.csv" in checksums
        assert "subdir/nested.csv" in checksums

    def test_non_recursive_scan(self, tmp_path):
        """Test non-recursive scanning."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        (tmp_path / "root.csv").write_text("root")
        (subdir / "nested.csv").write_text("nested")

        checksums = calculate_directory_checksums(tmp_path, recursive=False)

        assert len(checksums) == 1
        assert "root.csv" in checksums
        assert "subdir/nested.csv" not in checksums

    def test_directory_not_found(self):
        """Test that FileNotFoundError is raised for missing directory."""
        with pytest.raises(FileNotFoundError):
            calculate_directory_checksums(Path("/non/existent/dir"))

    def test_path_is_file(self, tmp_path):
        """Test that NotADirectoryError is raised if path is a file."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")
        
        with pytest.raises(NotADirectoryError):
            calculate_directory_checksums(test_file)


class TestJsonPersistence:
    """Tests for JSON serialization and deserialization."""

    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums to/from JSON."""
        checksums = {
            "file1.csv": "abc123...",
            "file2.json": "def456..."
        }
        
        output_path = tmp_path / "checksums.json"
        save_checksums_to_json(checksums, output_path)
        
        assert output_path.exists()
        
        loaded = load_checksums_from_json(output_path)
        
        assert loaded == checksums

    def test_load_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing JSON file."""
        with pytest.raises(FileNotFoundError):
            load_checksums_from_json(tmp_path / "missing.json")

    def test_load_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            load_checksums_from_json(invalid_json)


class TestVerifyChecksums:
    """Tests for checksum verification."""

    def test_verify_all_valid(self, tmp_path):
        """Test verification when all files match."""
        # Create files
        file1 = tmp_path / "file1.csv"
        file1.write_text("data1")
        
        # Calculate actual hash
        actual_hash = calculate_file_sha256(file1)
        
        checksums = {"file1.csv": actual_hash}
        
        results = verify_checksums(tmp_path, checksums)
        
        assert results["file1.csv"] is True

    def test_verify_mismatch(self, tmp_path):
        """Test verification when hash does not match."""
        file1 = tmp_path / "file1.csv"
        file1.write_text("data1")
        
        checksums = {"file1.csv": "wronghash12345678901234567890123456789012345678901234567890"}
        
        results = verify_checksums(tmp_path, checksums)
        
        assert results["file1.csv"] is False

    def test_verify_missing_file(self, tmp_path):
        """Test verification when file is missing."""
        checksums = {"missing_file.csv": "abc123..."}
        
        results = verify_checksums(tmp_path, checksums)
        
        assert results["missing_file.csv"] is False


class TestGenerateRawDataChecksums:
    """Tests for the raw data checksum generator."""

    def test_generate_with_existing_directory(self, tmp_path):
        """Test generating checksums when directory exists."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        (data_dir / "test.csv").write_text("a,b\n1,2")
        
        checksums = generate_raw_data_checksums(data_dir)
        
        assert len(checksums) == 1
        assert "test.csv" in checksums

    def test_generate_with_empty_directory(self, tmp_path):
        """Test generating checksums for empty directory."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        checksums = generate_raw_data_checksums(data_dir)
        
        assert checksums == {}

    def test_generate_with_nonexistent_directory(self, tmp_path):
        """Test generating checksums for non-existent directory."""
        data_dir = tmp_path / "nonexistent"
        
        checksums = generate_raw_data_checksums(data_dir)
        
        assert checksums == {}

    def test_generate_with_output_file(self, tmp_path):
        """Test generating checksums and saving to output file."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        (data_dir / "test.csv").write_text("data")
        
        output_file = tmp_path / "output.json"
        
        checksums = generate_raw_data_checksums(data_dir, output_file)
        
        assert output_file.exists()
        assert len(checksums) == 1