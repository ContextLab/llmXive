"""
Unit tests for the logging infrastructure.

Verifies JSON log format, error handling patterns, and logger initialization.
"""
import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logging import (
    JSONFormatter,
    get_logger,
    log_error,
    setup_logging,
)


class TestJSONFormatter:
    """Tests for the custom JSON log formatter."""

    def test_format_basic_info(self):
        """Test formatting a basic INFO log record."""
        formatter = JSONFormatter()
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

    def test_format_with_exception(self):
        """Test formatting a log record with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except Exception:
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

        assert parsed["level"] == "ERROR"
        assert "exc_info" in parsed
        assert parsed["exc_info"]["type"] == "ValueError"
        assert "traceback" in parsed["exc_info"]


class TestSetupLogging:
    """Tests for logging initialization."""

    def test_setup_console_only(self):
        """Test setup with console output only."""
        logger = setup_logging(console=True, level=logging.DEBUG)
        assert logger is not None
        assert logger.name == "born_model"
        assert len(logger.handlers) >= 1

    def test_setup_with_file(self):
        """Test setup with both file and console output."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            logger = setup_logging(log_file=tmp_path, console=False)
            assert logger is not None

            # Verify file handler exists
            file_handlers = [
                h for h in logger.handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) == 1

            # Write a test log
            logger.info("Test message")

            # Verify file was written
            assert os.path.exists(tmp_path)
            with open(tmp_path, "r") as f:
                content = f.read()
                assert "Test message" in content
                # Verify JSON format
                parsed = json.loads(content.strip())
                assert parsed["message"] == "Test message"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_setup_creates_parent_dirs(self):
        """Test that setup_logging creates parent directories for log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "subdir" / "logs" / "test.log"

            logger = setup_logging(log_file=str(log_path), console=False)
            assert logger is not None
            assert log_path.exists()


class TestGetLogger:
    """Tests for retrieving the logger."""

    def test_get_logger_after_setup(self):
        """Test that get_logger returns the configured logger."""
        setup_logging(console=False)
        logger = get_logger()
        assert logger.name == "born_model"

    def test_get_logger_before_setup_raises(self):
        """Test that get_logger raises RuntimeError if not initialized."""
        # Reset the module-level logger
        import code.utils.logging as logging_module
        logging_module._logger = None

        with pytest.raises(RuntimeError, match="Logging not initialized"):
            get_logger()


class TestLogError:
    """Tests for the log_error helper function."""

    def test_log_error_without_exception(self):
        """Test logging an error without exception details."""
        logger = setup_logging(console=False)
        logger.handlers.clear()

        # Add a custom handler to capture output
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        log_error(logger, "Test error message")

        output = stream.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "Test error message"

    def test_log_error_with_exception(self):
        """Test logging an error with exception details."""
        logger = setup_logging(console=False)
        logger.handlers.clear()

        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        try:
            raise ValueError("Test exception")
        except Exception as e:
            log_error(logger, "An error occurred", exception=e)

        output = stream.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["level"] == "ERROR"
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert "traceback" in parsed["exception"]
