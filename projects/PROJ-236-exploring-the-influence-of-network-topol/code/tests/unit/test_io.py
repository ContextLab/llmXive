"""
Unit tests for I/O utilities, specifically checksumming.
"""
import tempfile
from pathlib import Path

import pytest

from utils.io import compute_file_checksum, verify_file_checksum


class TestChecksumming:
    """Tests for checksumming utility functions."""

    def test_compute_checksum_sha256(self):
        """Test that compute_file_checksum generates a valid SHA-256 hash."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path, algorithm="sha256")
            # SHA-256 produces a 64-character hex string
            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)
        finally:
            temp_path.unlink()

    def test_compute_checksum_md5(self):
        """Test that compute_file_checksum works with MD5."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test data")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path, algorithm="md5")
            # MD5 produces a 32-character hex string
            assert len(checksum) == 32
        finally:
            temp_path.unlink()

    def test_compute_checksum_reproducible(self):
        """Test that checksum is consistent across multiple calls."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Reproducible content")
            temp_path = Path(f.name)

        try:
            checksum1 = compute_file_checksum(temp_path)
            checksum2 = compute_file_checksum(temp_path)
            assert checksum1 == checksum2
        finally:
            temp_path.unlink()

    def test_verify_checksum_match(self):
        """Test verify_file_checksum returns True for matching checksums."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Verify this")
            temp_path = Path(f.name)

        try:
            expected = compute_file_checksum(temp_path)
            assert verify_file_checksum(temp_path, expected) is True
        finally:
            temp_path.unlink()

    def test_verify_checksum_mismatch(self):
        """Test verify_file_checksum returns False for mismatched checksums."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Wrong content")
            temp_path = Path(f.name)

        try:
            # Compute checksum for different content
            wrong_expected = compute_file_checksum(temp_path)
            # Now change file content
            with open(temp_path, "w") as f:
                f.write("Different content")

            assert verify_file_checksum(temp_path, wrong_expected) is False
        finally:
            temp_path.unlink()

    def test_verify_missing_file(self):
        """Test verify_file_checksum returns False for missing file."""
        missing_path = Path("/tmp/nonexistent_file_xyz_12345.txt")
        assert verify_file_checksum(missing_path, "some_checksum") is False

    def test_compute_missing_file_raises(self):
        """Test compute_file_checksum raises FileNotFoundError for missing file."""
        missing_path = Path("/tmp/nonexistent_file_xyz_12345.txt")
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_path)

    def test_compute_unsupported_algorithm_raises(self):
        """Test compute_file_checksum raises ValueError for unsupported algorithm."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Data")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError):
                compute_file_checksum(temp_path, algorithm="blake2b")
        finally:
            temp_path.unlink()
