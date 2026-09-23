"""
Unit tests for checksum verification utilities.
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from utils.checksum import verify_file, compute_file_hash


class TestVerifyFile:
    """Tests for the verify_file function."""

    def test_verify_file_success(self, tmp_path):
        """Test successful verification with correct hash."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        # Compute the correct hash
        correct_hash = compute_file_hash(str(test_file))

        # Verify should return True
        assert verify_file(str(test_file), correct_hash) is True

    def test_verify_file_failure(self, tmp_path):
        """Test verification fails with incorrect hash."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Hello, World!")

        # Use an incorrect hash
        wrong_hash = "a" * 64

        # Verify should return False
        assert verify_file(str(test_file), wrong_hash) is False

    def test_verify_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            verify_file("/nonexistent/path/file.txt", "a" * 64)

    def test_verify_file_invalid_hash_format(self, tmp_path):
        """Test that ValueError is raised for invalid hash format."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        # Invalid hash formats
        invalid_hashes = [
            "short",  # Too short
            "a" * 63,  # Wrong length
            "a" * 65,  # Wrong length
            "xyz" * 21 + "1",  # Invalid hex characters
            "A" * 64,  # Uppercase is actually valid, so this won't fail
        ]

        # Test non-hex characters
        with pytest.raises(ValueError):
            verify_file(str(test_file), "xyz" * 21 + "1")

        # Test wrong length
        with pytest.raises(ValueError):
            verify_file(str(test_file), "a" * 63)

    def test_verify_file_case_insensitive(self, tmp_path):
        """Test that hash comparison is case-insensitive."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        correct_hash = compute_file_hash(str(test_file))
        upper_hash = correct_hash.upper()

        # Should work with uppercase
        assert verify_file(str(test_file), upper_hash) is True

    def test_verify_file_large_file(self, tmp_path):
        """Test verification with a larger file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        test_content = b"x" * (1024 * 1024)
        test_file.write_bytes(test_content)

        correct_hash = compute_file_hash(str(test_file))

        assert verify_file(str(test_file), correct_hash) is True


class TestComputeFileHash:
    """Tests for the compute_file_hash function."""

    def test_compute_sha256(self, tmp_path):
        """Test SHA256 hash computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        hash_result = compute_file_hash(str(test_file), 'sha256')

        # SHA256 produces 64 hex characters
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)

    def test_compute_md5(self, tmp_path):
        """Test MD5 hash computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        hash_result = compute_file_hash(str(test_file), 'md5')

        # MD5 produces 32 hex characters
        assert len(hash_result) == 32

    def test_compute_sha512(self, tmp_path):
        """Test SHA512 hash computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        hash_result = compute_file_hash(str(test_file), 'sha512')

        # SHA512 produces 128 hex characters
        assert len(hash_result) == 128

    def test_compute_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash("/nonexistent/file.txt")

    def test_compute_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for unsupported algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        with pytest.raises(ValueError):
            compute_file_hash(str(test_file), 'invalid_algo')

    def test_deterministic_hash(self, tmp_path):
        """Test that hash computation is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"consistent content")

        hash1 = compute_file_hash(str(test_file))
        hash2 = compute_file_hash(str(test_file))

        assert hash1 == hash2