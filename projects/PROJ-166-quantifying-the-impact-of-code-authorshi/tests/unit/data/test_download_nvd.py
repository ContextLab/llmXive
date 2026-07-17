import os
import gzip
import hashlib
import json
import tempfile
from pathlib import Path
import pytest

from data.download_nvd import calculate_sha256, generate_checksum


class TestNVDChecksumVerification:
    """Tests for NVD checksum verification logic."""

    def test_calculate_sha256_on_known_content(self, tmp_path):
        """Assert SHA256 matches expected value for known content."""
        # Create a temporary file with known content
        test_content = b"Hello, World! This is a test."
        test_file = tmp_path / "test_file.json"
        test_file.write_bytes(test_content)

        # Calculate SHA256
        calculated_hash = calculate_sha256(str(test_file))

        # Expected SHA256 for "Hello, World! This is a test."
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert calculated_hash == expected_hash
        assert len(calculated_hash) == 64  # SHA256 hex is 64 characters

    def test_generate_checksum_format(self, tmp_path):
        """Test that generate_checksum produces valid checksum format."""
        test_content = b"Test data for checksum"
        test_file = tmp_path / "test_data.json"
        test_file.write_bytes(test_content)

        checksum = generate_checksum(str(test_file))

        # Verify format: hex string of length 64
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum.lower())

    def test_sha256_consistency(self, tmp_path):
        """Verify SHA256 calculation is consistent across multiple runs."""
        test_content = b"Consistency test data"
        test_file = tmp_path / "consistency_test.json"
        test_file.write_bytes(test_content)

        hash1 = calculate_sha256(str(test_file))
        hash2 = calculate_sha256(str(test_file))
        hash3 = calculate_sha256(str(test_file))

        assert hash1 == hash2 == hash3

    def test_different_content_different_hash(self, tmp_path):
        """Verify different content produces different hashes."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        file1.write_bytes(b"Content A")
        file2.write_bytes(b"Content B")

        hash1 = calculate_sha256(str(file1))
        hash2 = calculate_sha256(str(file2))

        assert hash1 != hash2

    def test_empty_file_hash(self, tmp_path):
        """Test SHA256 calculation on empty file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_bytes(b"")

        hash_value = calculate_sha256(str(empty_file))

        # SHA256 of empty string
        expected_empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_value == expected_empty_hash

    def test_large_file_hash(self, tmp_path):
        """Test SHA256 calculation on larger file."""
        large_content = b"x" * (1024 * 1024)  # 1MB of data
        large_file = tmp_path / "large.json"
        large_file.write_bytes(large_content)

        hash_value = calculate_sha256(str(large_file))

        # Verify it's a valid SHA256 hash
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value.lower())

    def test_gzip_file_hash(self, tmp_path):
        """Test SHA256 calculation on gzipped content."""
        original_content = b"Original content before compression"
        gz_file = tmp_path / "compressed.json.gz"

        with gzip.open(str(gz_file), 'wb') as f:
            f.write(original_content)

        hash_value = calculate_sha256(str(gz_file))

        # Verify it's a valid SHA256 hash
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value.lower())

    def test_binary_content_hash(self, tmp_path):
        """Test SHA256 calculation on binary content."""
        binary_content = bytes(range(256))  # All possible byte values
        binary_file = tmp_path / "binary.json"
        binary_file.write_bytes(binary_content)

        hash_value = calculate_sha256(str(binary_file))

        # Verify it's a valid SHA256 hash
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value.lower())

    def test_unicode_content_hash(self, tmp_path):
        """Test SHA256 calculation on unicode content."""
        unicode_content = "Hello 世界 🌍 مرحبا".encode('utf-8')
        unicode_file = tmp_path / "unicode.json"
        unicode_file.write_bytes(unicode_content)

        hash_value = calculate_sha256(str(unicode_file))

        # Verify it's a valid SHA256 hash
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value.lower())