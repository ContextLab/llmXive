"""
Unit tests for the logging infrastructure.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.logger import (
    LOG_FILE,
    JsonFormatter,
    get_logger,
    info,
    error,
    log_with_context,
    setup_logging,
)


class TestJsonFormatter:
    """Tests for the JSON log formatter."""

    def test_format_basic_record(self):
        """Test that basic log records are formatted as valid JSON."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert parsed["module"] == "test"

    def test_format_with_extra_data(self):
        """Test that extra context data is included in JSON output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value", "count": 42}

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["count"] == 42

    def test_format_with_exception(self):
        """Test that exception info is included when present."""
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_logger_creation(self):
        """Test that a logger is created and configured correctly."""
        logger = get_logger("test_logger_1")

        assert logger.name == "test_logger_1"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2  # File and console

    def test_logger_reuse(self):
        """Test that calling get_logger multiple times returns the same instance."""
        logger1 = get_logger("test_logger_2")
        logger2 = get_logger("test_logger_2")

        assert logger1 is logger2

    def test_log_directory_creation(self, tmp_path):
        """Test that the log directory is created if it doesn't exist."""
        with patch("src.utils.logger.LOG_DIR", str(tmp_path / "new_dir")):
            with patch("src.utils.logger.LOG_FILE", str(tmp_path / "new_dir" / "run.log")):
                logger = get_logger("test_logger_3")
                assert (tmp_path / "new_dir").exists()


class TestLogWithContext:
    """Tests for the log_with_context function."""

    def test_log_with_context_adds_data(self, tmp_path):
        """Test that context data is added to log records."""
        log_file = tmp_path / "test.log"
        with patch("src.utils.logger.LOG_FILE", str(log_file)):
            logger = get_logger("test_context_logger")
            # Clear handlers to use our test file
            logger.handlers.clear()

            file_handler = logging.FileHandler(str(log_file))
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

            log_with_context(
                logger,
                logging.INFO,
                "Test message",
                context={"user_id": 123, "action": "login"},
            )

            # Read the log file and verify
            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)

            assert parsed["data"]["user_id"] == 123
            assert parsed["data"]["action"] == "login"


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a configured logger."""
        logger = setup_logging()

        assert logger is not None
        assert len(logger.handlers) >= 2

    def test_setup_logging_creates_log_file(self, tmp_path):
        """Test that setup_logging creates the log file directory."""
        log_dir = tmp_path / "artifacts"
        with patch("src.utils.logger.LOG_DIR", str(log_dir)):
            with patch("src.utils.logger.LOG_FILE", str(log_dir / "run.log")):
                setup_logging()
                assert log_dir.exists()


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_info_function(self, tmp_path):
        """Test the info() convenience function."""
        log_file = tmp_path / "test_info.log"
        with patch("src.utils.logger.LOG_FILE", str(log_file)):
            logger = get_logger("test_info")
            logger.handlers.clear()

            file_handler = logging.FileHandler(str(log_file))
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

            info("Test info message", context={"test": True})

            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)

            assert parsed["level"] == "INFO"
            assert parsed["message"] == "Test info message"
            assert parsed["data"]["test"] is True

    def test_error_function(self, tmp_path):
        """Test the error() convenience function."""
        log_file = tmp_path / "test_error.log"
        with patch("src.utils.logger.LOG_FILE", str(log_file)):
            logger = get_logger("test_error")
            logger.handlers.clear()

            file_handler = logging.FileHandler(str(log_file))
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

            error("Test error message", context={"error_code": 500})

            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)

            assert parsed["level"] == "ERROR"
            assert parsed["message"] == "Test error message"
            assert parsed["data"]["error_code"] == 500