"""
Unit tests for the validation module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.validation import (
    compute_md5,
    validate_checksum,
    get_file_size,
    validate_file_exists,
    validate_file_not_empty,
)


class TestComputeMD5:
    def test_compute_md5_small_file(self, tmp_path):
        """Test MD5 computation on a small file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = compute_md5(test_file)

        # Known MD5 for "Hello, World!"
        assert checksum == "65a8e27d8879283831b664bd8b7f0ad4"

    def test_compute_md5_empty_file(self, tmp_path):
        """Test MD5 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        checksum = compute_md5(test_file)

        # MD5 of empty string
        assert checksum == "d41d8cd98f00b204e9800998ecf8427e"

    def test_compute_md5_large_file(self, tmp_path):
        """Test MD5 computation on a larger file."""
        test_file = tmp_path / "large.bin"
        # Create a file with known content
        content = b"X" * 100000
        test_file.write_bytes(content)

        checksum = compute_md5(test_file)

        # Verify it's a valid hex string of correct length
        assert len(checksum) == 32
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_compute_md5_nonexistent_file(self):
        """Test that compute_md5 raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_md5("/nonexistent/path/file.txt")

    def test_compute_md5_directory(self, tmp_path):
        """Test that compute_md5 raises IsADirectoryError for directories."""
        with pytest.raises(IsADirectoryError):
            compute_md5(tmp_path)


class TestValidateChecksum:
    def test_validate_checksum_match(self, tmp_path):
        """Test validation when checksum matches."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test data")

        # Get actual checksum
        actual_checksum = compute_md5(test_file)

        is_valid, computed = validate_checksum(test_file, actual_checksum)

        assert is_valid is True
        assert computed == actual_checksum

    def test_validate_checksum_mismatch(self, tmp_path):
        """Test validation when checksum does not match."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test data")

        fake_checksum = "00000000000000000000000000000000"

        is_valid, computed = validate_checksum(test_file, fake_checksum)

        assert is_valid is False
        assert computed != fake_checksum

    def test_validate_checksum_case_insensitive(self, tmp_path):
        """Test that checksum comparison is case-insensitive."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test data")

        actual_checksum = compute_md5(test_file)
        upper_checksum = actual_checksum.upper()

        is_valid, _ = validate_checksum(test_file, upper_checksum)

        assert is_valid is True


class TestGetFileSize:
    def test_get_file_size(self, tmp_path):
        """Test getting file size."""
        test_file = tmp_path / "test.bin"
        content = b"0123456789"  # 10 bytes
        test_file.write_bytes(content)

        size = get_file_size(test_file)

        assert size == 10

    def test_get_file_size_nonexistent(self):
        """Test that get_file_size raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            get_file_size("/nonexistent/file.txt")


class TestValidateFileExists:
    def test_validate_file_exists_true(self, tmp_path):
        """Test validation when file exists."""
        test_file = tmp_path / "exists.txt"
        test_file.write_bytes(b"data")

        assert validate_file_exists(test_file) is True

    def test_validate_file_exists_false(self, tmp_path):
        """Test validation when file does not exist."""
        assert validate_file_exists(tmp_path / "nonexistent.txt") is False


class TestValidateFileNotEmpty:
    def test_validate_file_not_empty_true(self, tmp_path):
        """Test validation when file is not empty."""
        test_file = tmp_path / "notempty.txt"
        test_file.write_bytes(b"data")

        assert validate_file_not_empty(test_file) is True

    def test_validate_file_not_empty_false_empty(self, tmp_path):
        """Test validation when file is empty."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        assert validate_file_not_empty(test_file) is False

    def test_validate_file_not_empty_false_missing(self, tmp_path):
        """Test validation when file is missing."""
        assert validate_file_not_empty(tmp_path / "missing.txt") is False
