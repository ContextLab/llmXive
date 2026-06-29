"""
Tests for the pipeline utility functions in code/pipeline/utils.py.
"""

import hashlib
import os
import random
import tempfile
from pathlib import Path

import pytest

from code.pipeline.utils import compute_checksum, set_global_seed, setup_logger


class TestSetupLogger:
    """Tests for the setup_logger function."""

    def test_logger_creation(self, tmp_path):
        """Test that a logger is created successfully."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger", str(log_file))

        assert logger is not None
        assert logger.name == "test_logger"

    def test_logger_writes_to_file(self, tmp_path):
        """Test that the logger writes to the specified file."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file_logger", str(log_file))

        logger.info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_logger_console_output(self, caplog):
        """Test that the logger outputs to console."""
        logger = setup_logger("test_console_logger")

        with caplog.at_level("INFO"):
            logger.info("Console test message")

        assert "Console test message" in caplog.text

    def test_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't add duplicate handlers."""
        logger1 = setup_logger("test_no_dup")
        handler_count = len(logger1.handlers)

        logger2 = setup_logger("test_no_dup")

        assert len(logger2.handlers) == handler_count


class TestSetGlobalSeed:
    """Tests for the set_global_seed function."""

    def test_python_random_seed(self):
        """Test that Python's random module is seeded correctly."""
        set_global_seed(12345)
        val1 = random.random()

        set_global_seed(12345)
        val2 = random.random()

        assert val1 == val2

    def test_numpy_seed(self):
        """Test that NumPy is seeded correctly (if available)."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("NumPy not installed")

        set_global_seed(54321)
        arr1 = np.random.rand(5)

        set_global_seed(54321)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2)

    def test_hash_seed_environment(self):
        """Test that PYTHONHASHSEED is set."""
        set_global_seed(99999)
        assert os.environ.get("PYTHONHASHSEED") == "99999"


class TestComputeChecksum:
    """Tests for the compute_checksum function."""

    def test_checksum_calculation(self, tmp_path):
        """Test that checksum is calculated correctly."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_checksum(str(test_file))

        # Verify against hashlib directly
        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected

    def test_checksum_hex_format(self, tmp_path):
        """Test that checksum is in hexadecimal format."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test data")

        checksum = compute_checksum(str(test_file))

        # Should be 64 hex characters (SHA-256)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_checksum(str(tmp_path / "nonexistent.txt"))

    def test_directory_error(self, tmp_path):
        """Test that IsADirectoryError is raised for directories."""
        with pytest.raises(IsADirectoryError):
            compute_checksum(str(tmp_path))

    def test_large_file_handling(self, tmp_path):
        """Test that large files are handled correctly (chunked reading)."""
        test_file = tmp_path / "large.txt"
        # Create a 1MB file
        test_content = b"x" * (1024 * 1024)
        test_file.write_bytes(test_content)

        checksum = compute_checksum(str(test_file))

        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected