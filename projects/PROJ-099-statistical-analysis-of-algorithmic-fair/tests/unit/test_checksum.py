"""
Unit tests for checksum verification functionality.

This module tests the SHA-256 checksum computation and verification
functions provided by code/utils/validators.py and code/utils/dataset_loaders.py.
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import functions from the project's utility modules
from utils.validators import compute_sha256, verify_checksum
from utils.dataset_loaders import compute_sha256 as dl_compute_sha256


class TestComputeSha256:
    """Tests for the compute_sha256 function."""

    def test_compute_sha256_file_exists(self):
        """Test that compute_sha256 works on an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            hash_value = compute_sha256(temp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
            assert all(c in '0123456789abcdef' for c in hash_value)
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_file_not_found(self):
        """Test that compute_sha256 raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/to/file.txt")

    def test_compute_sha256_empty_file(self):
        """Test that compute_sha256 works on an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name

        try:
            hash_value = compute_sha256(temp_path)
            # SHA-256 of empty string is known
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert hash_value == expected
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_deterministic(self):
        """Test that compute_sha256 produces consistent results."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Deterministic test content")
            temp_path = f.name

        try:
            hash1 = compute_sha256(temp_path)
            hash2 = compute_sha256(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_from_dataset_loaders(self):
        """Test that the compute_sha256 from dataset_loaders works identically."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Cross-module test")
            temp_path = f.name

        try:
            hash1 = compute_sha256(temp_path)
            hash2 = dl_compute_sha256(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)


class TestVerifyChecksum:
    """Tests for the verify_checksum function."""

    def test_verify_checksum_matches(self):
        """Test that verify_checksum returns True when checksum matches."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Content for verification")
            temp_path = f.name

        try:
            actual_hash = compute_sha256(temp_path)
            is_valid = verify_checksum(temp_path, actual_hash)
            assert is_valid is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_mismatch(self):
        """Test that verify_checksum returns False when checksum doesn't match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Content for verification")
            temp_path = f.name

        try:
            # Use a known incorrect hash
            wrong_hash = "0" * 64
            is_valid = verify_checksum(temp_path, wrong_hash)
            assert is_valid is False
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_file_not_found(self):
        """Test that verify_checksum raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            verify_checksum("/nonexistent/file.txt", "some_hash")

    def test_verify_checksum_invalid_hash_format(self):
        """Test that verify_checksum raises ValueError for invalid hash format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                verify_checksum(temp_path, "invalid_hash_format")
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_case_insensitive(self):
        """Test that verify_checksum is case-insensitive for hash comparison."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Case test")
            temp_path = f.name

        try:
            actual_hash = compute_sha256(temp_path)
            upper_hash = actual_hash.upper()
            # Should work with uppercase
            is_valid_upper = verify_checksum(temp_path, upper_hash)
            assert is_valid_upper is True
        finally:
            os.unlink(temp_path)