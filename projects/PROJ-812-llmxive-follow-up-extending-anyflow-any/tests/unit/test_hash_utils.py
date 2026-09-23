"""
test_hash_utils.py
Unit tests for hash_utils.py functionality.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the functions from the sibling module
from code.utils.hash_utils import (
    compute_sha256,
    verify_sha256,
    hash_directory,
    save_checksums,
    load_checksums,
    verify_directory_integrity,
)


class TestComputeSha256:
    def test_compute_sha256_known_file(self, tmp_path):
        """Test hashing a file with a known content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # The SHA-256 of b"Hello, World!" is known
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

        result = compute_sha256(test_file)
        assert result == expected_hash

    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_directory(self, tmp_path):
        """Test that IsADirectoryError is raised for directories."""
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmp_path)


class TestVerifySha256:
    def test_verify_sha256_success(self, tmp_path):
        """Test successful verification."""
        test_file = tmp_path / "verify.txt"
        test_file.write_text("Verify me")
        
        # Compute actual hash first
        actual_hash = compute_sha256(test_file)
        
        assert verify_sha256(test_file, actual_hash) is True

    def test_verify_sha256_failure(self, tmp_path):
        """Test failed verification with wrong hash."""
        test_file = tmp_path / "verify_fail.txt"
        test_file.write_text("Wrong hash")
        
        wrong_hash = "0" * 64
        
        assert verify_sha256(test_file, wrong_hash) is False


class TestHashDirectory:
    def test_hash_directory_single_file(self, tmp_path):
        """Test hashing a directory with a single file."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        result = hash_directory(tmp_path)
        
        assert "file1.txt" in result
        assert len(result) == 1
        assert len(result["file1.txt"]) == 64  # SHA-256 length

    def test_hash_directory_with_pattern(self, tmp_path):
        """Test hashing a directory with a specific pattern."""
        (tmp_path / "file1.txt").write_text("Text")
        (tmp_path / "file2.bin").write_bytes(b"\x00\x01")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("Text 3")
        
        result = hash_directory(tmp_path, pattern="*.txt")
        
        assert "file1.txt" in result
        assert "subdir/file3.txt" in result
        assert "file2.bin" not in result
        assert len(result) == 2


class TestSaveLoadChecksums:
    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums."""
        checksums = {
            "file1.txt": "hash1",
            "file2.txt": "hash2",
        }
        output_path = tmp_path / "checksums.json"
        
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        
        loaded = load_checksums(output_path)
        
        assert loaded == checksums

    def test_load_missing_file(self, tmp_path):
        """Test loading from a non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_checksums(tmp_path / "missing.json")


class TestVerifyDirectoryIntegrity:
    def test_verify_integrity_success(self, tmp_path):
        """Test successful directory integrity verification."""
        # Create files
        file1 = tmp_path / "file1.txt"
        file1.write_text("Data 1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Data 2")
        
        # Create checksum file
        checksums = {
            "file1.txt": compute_sha256(file1),
            "file2.txt": compute_sha256(file2),
        }
        checksum_path = tmp_path / "checksums.json"
        save_checksums(checksums, checksum_path)
        
        # Verify
        failures = verify_directory_integrity(tmp_path, checksum_path)
        
        assert len(failures) == 0

    def test_verify_integrity_missing_file(self, tmp_path):
        """Test integrity check when a file is missing."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Data 1")
        
        checksums = {
            "file1.txt": compute_sha256(file1),
            "missing.txt": "somehash",
        }
        checksum_path = tmp_path / "checksums.json"
        save_checksums(checksums, checksum_path)
        
        failures = verify_directory_integrity(tmp_path, checksum_path)
        
        assert "missing.txt" in failures

    def test_verify_integrity_corrupted_file(self, tmp_path):
        """Test integrity check when a file is corrupted."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Original Data")
        
        checksums = {
            "file1.txt": compute_sha256(file1),
        }
        checksum_path = tmp_path / "checksums.json"
        save_checksums(checksums, checksum_path)
        
        # Corrupt the file
        file1.write_text("Corrupted Data")
        
        failures = verify_directory_integrity(tmp_path, checksum_path)
        
        assert "file1.txt" in failures