"""
Unit tests for utility modules (logger and checksum).
"""
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logger import get_logger, setup_logging
from code.utils.checksum import compute_file_checksum, verify_file_checksum


class TestChecksum:
    def test_compute_sha256(self):
        """Test SHA-256 computation on a known string."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            # Known SHA-256 for "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(Path("/non/existent/file.txt"))

    def test_verify_match(self):
        """Test verification when checksum matches."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test Data")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            assert verify_file_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_mismatch(self):
        """Test verification when checksum does not match."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test Data")
            temp_path = Path(f.name)

        try:
            bad_checksum = "0000000000000000000000000000000000000000000000000000000000000000"
            assert verify_file_checksum(temp_path, bad_checksum) is False
        finally:
            os.unlink(temp_path)


class TestLogger:
    def test_setup_logging_console_only(self, caplog):
        """Test console logging setup."""
        setup_logging(level=logging.INFO)
        logger = get_logger("test_console")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text

    def test_setup_logging_with_file(self, tmp_path):
        """Test file logging setup."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, level=logging.INFO)
        logger = get_logger("test_file")

        logger.info("File log message")

        assert log_file.exists()
        with open(log_file, "r") as f:
            content = f.read()
        assert "File log message" in content

    def test_get_logger_name(self):
        """Test that logger returns correct name."""
        logger = get_logger("custom_name")
        assert logger.name == "custom_name"
