"""
Unit tests for the structured logging utility.
"""
import pytest
import logging
import json
import sys
from io import StringIO
from pathlib import Path
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import (
    get_logger,
    setup_logging,
    info,
    warning,
    error,
    debug,
    critical,
    log_with_context,
    StructuredFormatter
)


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""

    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert "module" in parsed
        assert "function" in parsed
        assert "line" in parsed

    def test_format_with_exception(self):
        """Test formatting a log message with an exception."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "Error occurred"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_format_with_extra_data(self):
        """Test formatting a log message with extra context data."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Context test",
            args=(),
            exc_info=None
        )
        record.extra_data = {"subject_id": 123, "metric": "efficiency"}

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "Context test"
        assert parsed["data"]["subject_id"] == 123
        assert parsed["data"]["metric"] == "efficiency"


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_creates_instance(self):
        """Test that get_logger creates a new logger instance."""
        logger = get_logger("test_get_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_get_logger"

    def test_get_logger_reuses_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")
        assert logger1 is logger2

    def test_get_logger_has_console_handler(self):
        """Test that the logger has a console handler."""
        logger = get_logger("test_handler")
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0], logging.StreamHandler)


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_console_only(self, tmp_path):
        """Test setup_logging with only console output."""
        os.environ["STRUCTURED_LOGGING"] = "false"
        logger = setup_logging(log_level="DEBUG")

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self, tmp_path):
        """Test setup_logging with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file)

        assert len(logger.handlers) == 2  # Console + File
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert log_file.exists()

    def test_setup_logging_structured(self):
        """Test setup_logging with structured formatting."""
        os.environ["STRUCTURED_LOGGING"] = "true"
        logger = setup_logging(structured=True)

        assert len(logger.handlers) > 0
        formatter = logger.handlers[0].formatter
        assert isinstance(formatter, StructuredFormatter)

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        nested_log_file = tmp_path / "subdir" / "test.log"
        logger = setup_logging(log_file=nested_log_file)

        assert nested_log_file.parent.exists()
        assert nested_log_file.exists()


class TestLogFunctions:
    """Tests for the convenience logging functions."""

    def test_info_logging(self, caplog):
        """Test the info() function."""
        with caplog.at_level(logging.INFO):
            info("Test info message")
            assert any("Test info message" in record.message for record in caplog.records)

    def test_warning_logging(self, caplog):
        """Test the warning() function."""
        with caplog.at_level(logging.WARNING):
            warning("Test warning message")
            assert any("Test warning message" in record.message for record in caplog.records)

    def test_error_logging(self, caplog):
        """Test the error() function."""
        with caplog.at_level(logging.ERROR):
            error("Test error message")
            assert any("Test error message" in record.message for record in caplog.records)

    def test_debug_logging(self, caplog):
        """Test the debug() function."""
        with caplog.at_level(logging.DEBUG):
            debug("Test debug message")
            assert any("Test debug message" in record.message for record in caplog.records)

    def test_critical_logging(self, caplog):
        """Test the critical() function."""
        with caplog.at_level(logging.CRITICAL):
            critical("Test critical message")
            assert any("Test critical message" in record.message for record in caplog.records)

    def test_log_with_context(self, caplog):
        """Test logging with additional context data."""
        with caplog.at_level(logging.INFO):
            logger = get_logger("test_context")
            log_with_context(logger, logging.INFO, "Context test", key="value")
            # Note: Context data is handled by the custom formatter, so we just verify
            # the message is logged
            assert any("Context test" in record.message for record in caplog.records)
