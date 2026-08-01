"""
Unit tests for code/utils.py utility functions.
Tests logging, checksums, and versioning.
"""
import pytest
import hashlib
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import (
    compute_sha256,
    verify_checksum,
    get_version,
    get_timestamp
)


class TestChecksum:
    def test_compute_sha256_string(self):
        """Test SHA-256 computation for a string."""
        test_string = "Hello, World!"
        expected_hash = hashlib.sha256(test_string.encode()).hexdigest()

        result = compute_sha256(test_string)
        assert result == expected_hash

    def test_compute_sha256_bytes(self):
        """Test SHA-256 computation for bytes."""
        test_bytes = b"Hello, World!"
        expected_hash = hashlib.sha256(test_bytes).hexdigest()

        result = compute_sha256(test_bytes)
        assert result == expected_hash

    def test_verify_checksum_valid(self):
        """Test checksum verification with valid hash."""
        data = "Test data for verification"
        hash_val = compute_sha256(data)

        assert verify_checksum(data, hash_val) is True

    def test_verify_checksum_invalid(self):
        """Test checksum verification with invalid hash."""
        data = "Test data for verification"
        invalid_hash = "a" * 64

        assert verify_checksum(data, invalid_hash) is False

    def test_compute_sha256_file(self):
        """Test SHA-256 computation for a file."""
        with patch('code.utils.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_bytes.return_value = b"File content"
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            expected_hash = hashlib.sha256(b"File content").hexdigest()
            result = compute_sha256(Path("test.txt"))

            assert result == expected_hash


class TestVersioning:
    def test_get_version(self):
        """Test version retrieval."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_timestamp(self):
        """Test timestamp generation."""
        timestamp = get_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Should be in ISO format or similar
        assert 'T' in timestamp or '-' in timestamp


class TestLogging:
    def test_logging_setup(self):
        """Test that logging is properly configured."""
        from code.utils import setup_logging, log_info, log_warning, log_error

        logger = setup_logging("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_log_functions_exist(self):
        """Test that log functions exist and are callable."""
        from code.utils import log_info, log_debug, log_warning, log_error, log_critical

        assert callable(log_info)
        assert callable(log_debug)
        assert callable(log_warning)
        assert callable(log_error)
        assert callable(log_critical)
