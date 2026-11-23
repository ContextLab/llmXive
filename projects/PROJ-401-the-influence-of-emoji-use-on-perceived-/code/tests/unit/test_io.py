"""
Unit tests for src/utils/io.py
"""

import logging
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.utils.io import (
    compute_file_checksum,
    configure_logging,
    ensure_directory,
    set_global_seed,
    verify_checksum,
)


class TestSetGlobalSeed:
    def test_seed_reproducibility(self):
        """Test that setting the seed produces reproducible random numbers."""
        set_global_seed(42)
        val1 = [random.random() for _ in range(5)]

        set_global_seed(42)
        val2 = [random.random() for _ in range(5)]

        assert val1 == val2

        # Different seed should produce different values
        set_global_seed(123)
        val3 = [random.random() for _ in range(5)]
        assert val1 != val3


class TestConfigureLogging:
    def test_console_logging(self):
        """Test that logging is configured for console output."""
        logger = configure_logging(level=logging.INFO, log_file=None)
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1  # Only console handler

    def test_file_logging(self):
        """Test that logging is configured for file output."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            log_path = tmp.name

        try:
            logger = configure_logging(level=logging.INFO, log_file=log_path)
            assert len(logger.handlers) == 2  # Console + File

            logger.info("Test message")
            with open(log_path, "r") as f:
                content = f.read()
            assert "Test message" in content
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)


class TestComputeFileChecksum:
    def test_sha256_checksum(self):
        """Test SHA256 checksum computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("Hello, World!")
            tmp_path = tmp.name

        try:
            checksum = compute_file_checksum(tmp_path, algorithm="sha256")
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.remove(tmp_path)

    def test_md5_checksum(self):
        """Test MD5 checksum computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("Hello, World!")
            tmp_path = tmp.name

        try:
            checksum = compute_file_checksum(tmp_path, algorithm="md5")
            assert len(checksum) == 32  # MD5 hex length
        finally:
            os.remove(tmp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("nonexistent_file.txt")

    def test_invalid_algorithm(self):
        """Test that ValueError is raised for unsupported algorithm."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("Test")
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError):
                compute_file_checksum(tmp_path, algorithm="invalid_algo")
        finally:
            os.remove(tmp_path)


class TestVerifyChecksum:
    def test_valid_checksum(self):
        """Test verification with valid checksum."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("Test data")
            tmp_path = tmp.name

        try:
            checksum = compute_file_checksum(tmp_path)
            assert verify_checksum(tmp_path, checksum) is True
        finally:
            os.remove(tmp_path)

    def test_invalid_checksum(self):
        """Test verification with invalid checksum."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("Test data")
            tmp_path = tmp.name

        try:
            assert verify_checksum(tmp_path, "invalid_checksum") is False
        finally:
            os.remove(tmp_path)


class TestEnsureDirectory:
    def test_create_new_directory(self):
        """Test creation of a new directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            new_dir = Path(tmp_dir) / "new_subdir"
            result = ensure_directory(new_dir)
            assert result.exists()
            assert result.is_dir()

    def test_existing_directory(self):
        """Test that existing directory is returned without error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = ensure_directory(tmp_dir)
            assert result.exists()
            assert result.is_dir()
