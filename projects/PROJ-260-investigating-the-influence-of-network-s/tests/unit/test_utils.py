"""
Unit tests for src/lib/utils.py
"""
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from src.lib.utils import (
    compute_sha256,
    verify_checksum,
    setup_logging,
    set_seed,
    validate_file_exists,
    validate_file_not_empty,
    ensure_directory,
    get_file_size_mb
)


class TestChecksumVerification:
    def test_compute_sha256_simple(self, tmp_path):
        """Test SHA256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = compute_sha256(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_compute_sha256_nonexistent(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(missing_file)

    def test_verify_checksum_match(self, tmp_path):
        """Test checksum verification when values match."""
        test_file = tmp_path / "test.txt"
        content = b"Test content"
        test_file.write_bytes(content)

        checksum = compute_sha256(test_file)
        assert verify_checksum(test_file, checksum) is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum verification when values differ."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        fake_checksum = "0" * 64
        assert verify_checksum(test_file, fake_checksum) is False

    def test_verify_checksum_nonexistent_file(self, tmp_path):
        """Test checksum verification for missing file."""
        missing_file = tmp_path / "missing.txt"
        assert verify_checksum(missing_file, "0" * 64) is False


class TestLoggingSetup:
    def test_setup_logging_console_only(self, tmp_path):
        """Test logging setup with console only."""
        logger = setup_logging(level=logging.DEBUG, name="test_console")
        assert logger.level == logging.DEBUG
        # Check that a console handler exists
        console_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) > 0

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file handler."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, level=logging.INFO, name="test_file")

        file_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) > 0
        assert log_file.exists()

    def test_setup_logging_duplicate_call(self):
        """Test that calling setup_logging again doesn't duplicate handlers."""
        logger = setup_logging(level=logging.INFO, name="test_dup")
        initial_count = len(logger.handlers)
        # Call again
        setup_logging(level=logging.INFO, name="test_dup")
        assert len(logger.handlers) == initial_count


class TestSeedManagement:
    def test_set_seed_reproducibility(self):
        """Test that set_seed produces reproducible results."""
        seed = 42
        set_seed(seed)
        val1 = np.random.random()
        val2 = random.random()

        set_seed(seed)
        val3 = np.random.random()
        val4 = random.random()

        assert val1 == val3
        assert val2 == val4

    def test_set_seed_return_value(self):
        """Test that set_seed returns the expected dictionary."""
        seed = 123
        result = set_seed(seed)
        assert result["seed"] == seed
        assert "status" in result


class TestFileValidation:
    def test_validate_file_exists_success(self, tmp_path):
        """Test validation passes for existing file."""
        test_file = tmp_path / "exists.txt"
        test_file.write_text("content")
        # Should not raise
        validate_file_exists(test_file)

    def test_validate_file_exists_fail(self, tmp_path):
        """Test validation fails for missing file."""
        missing_file = tmp_path / "missing.txt"
        with pytest.raises(ValueError, match="Required file not found"):
            validate_file_exists(missing_file)

    def test_validate_file_not_empty_success(self, tmp_path):
        """Test validation passes for non-empty file."""
        test_file = tmp_path / "nonempty.txt"
        test_file.write_text("content")
        validate_file_not_empty(test_file)

    def test_validate_file_not_empty_fail_empty(self, tmp_path):
        """Test validation fails for empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        with pytest.raises(ValueError, match="File is empty"):
            validate_file_not_empty(empty_file)

    def test_validate_file_not_empty_fail_missing(self, tmp_path):
        """Test validation fails for missing file."""
        missing_file = tmp_path / "missing.txt"
        with pytest.raises(ValueError, match="Required file not found"):
            validate_file_not_empty(missing_file)

    def test_ensure_directory_creates_new(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path):
        """Test that ensure_directory works on existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_directory(existing_dir)  # Should not raise
        assert existing_dir.exists()

    def test_get_file_size_mb(self, tmp_path):
        """Test file size calculation."""
        test_file = tmp_path / "size.txt"
        # Write 1024 bytes (1 KB)
        test_file.write_bytes(b"x" * 1024)
        size_mb = get_file_size_mb(test_file)
        expected_mb = 1024 / (1024 * 1024)
        assert abs(size_mb - expected_mb) < 1e-9

    def test_get_file_size_mb_missing(self, tmp_path):
        """Test get_file_size_mb raises for missing file."""
        missing_file = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            get_file_size_mb(missing_file)
