"""
Unit tests for the structured logging infrastructure.
"""

import pytest
import logging
from pathlib import Path
import tempfile
import os

from code.src.utils.logger import (
    get_error_message,
    AuditLogger,
    get_default_logger,
    configure_logging,
    ERROR_CODES
)


class TestErrorCodes:
    """Tests for error code formatting."""

    def test_known_error_codes(self):
        """Test that known error codes return the correct format."""
        assert get_error_message(1) == "ERR-001"
        assert get_error_message(10) == "ERR-010"
        assert get_error_message(100) == "ERR-100"
        assert get_error_message(301) == "ERR-301"
        assert get_error_message(800) == "ERR-800"

    def test_unknown_error_codes(self):
        """Test that unknown error codes are formatted correctly."""
        assert get_error_message(999) == "ERR-999"
        assert get_error_message(1234) == "ERR-1234"

    def test_error_code_format(self):
        """Test that all error codes follow the ERR-### format."""
        for code, expected in ERROR_CODES.items():
            assert expected.startswith("ERR-")
            assert len(expected) == 7  # ERR-###
            assert expected[4:].isdigit()


class TestAuditLogger:
    """Tests for the AuditLogger class."""

    def test_log_error_includes_code(self):
        """Test that error logs include the error code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            # Capture log output
            with open(log_file, 'w') as f:
                pass  # Clear file

            logger.log_error(1, "Test error message")

            # Read log file and verify format
            with open(log_file, 'r') as f:
                content = f.read()
                assert "ERR-001" in content
                assert "Test error message" in content

    def test_log_warning_with_code(self):
        """Test that warning logs with codes include the error code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            logger.log_warning(10, "Test warning message")

            with open(log_file, 'r') as f:
                content = f.read()
                assert "ERR-010" in content
                assert "Test warning message" in content

    def test_log_warning_without_code(self):
        """Test that warning logs without codes don't include error code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            logger.log_warning(None, "Test warning without code")

            with open(log_file, 'r') as f:
                content = f.read()
                assert "ERR-" not in content
                assert "Test warning without code" in content

    def test_log_info(self):
        """Test that info logs work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            logger.log_info("Test info message")

            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test info message" in content
                assert "ERR-" not in content

    def test_log_debug(self):
        """Test that debug logs work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            logger.log_debug("Test debug message")

            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test debug message" in content

    def test_log_success(self):
        """Test that success logs work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            logger.log_success(1, "Test success message")

            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test success message" in content

    def test_context_in_logging(self):
        """Test that context is included in log messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AuditLogger("test_logger", log_file)

            logger.log_error(1, "Test error", key1="value1", key2="value2")

            with open(log_file, 'r') as f:
                content = f.read()
                assert "ERR-001" in content
                assert "key1" in content
                assert "value1" in content


class TestGetDefaultLogger:
    """Tests for the get_default_logger function."""

    def test_returns_audit_logger(self):
        """Test that get_default_logger returns an AuditLogger instance."""
        logger = get_default_logger()
        assert isinstance(logger, AuditLogger)

    def test_returns_same_instance(self):
        """Test that get_default_logger returns the same instance on multiple calls."""
        logger1 = get_default_logger()
        logger2 = get_default_logger()
        assert logger1 is logger2


class TestConfigureLogging:
    """Tests for the configure_logging function."""

    def test_sets_log_level(self):
        """Test that configure_logging sets the log level correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            configure_logging("DEBUG", log_file)

            # Check that root logger has the correct level
            assert logging.getLogger().level == logging.DEBUG

    def test_creates_file_handler(self):
        """Test that configure_logging creates a file handler when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            configure_logging("INFO", log_file)

            # Check that the file exists
            assert log_file.exists()

    def test_no_file_handler_when_none(self):
        """Test that configure_logging doesn't create a file handler when log_file is None."""
        configure_logging("INFO", None)
        # Just verify it doesn't raise an exception
        assert True
