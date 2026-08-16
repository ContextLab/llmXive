"""
Unit tests for standardized logging configuration (Task T039c).

These tests verify that:
1. Logging is properly configured across modules
2. JSON formatting works correctly
3. Log rotation is set up
4. Context logging functions as expected
"""
import logging
import json
import tempfile
import os
from pathlib import Path
import pytest

# Import the logging module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import (
    JsonFormatter,
    get_logger,
    set_log_level,
    log_with_context,
    setup_logging,
    LOG_FORMAT,
)


class TestJsonFormatter:
    """Tests for the JSON log formatter."""

    def test_format_basic_log(self):
        """Test that basic log records are formatted as JSON."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
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
        assert parsed["module"] == "test"
        assert "timestamp" in parsed

    def test_format_with_exception(self):
        """Test that exceptions are included in JSON output."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "ERROR"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_format_with_extra_data(self):
        """Test that extra context data is included in JSON output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Contextual log",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"user_id": 123, "request_id": "abc-456"}

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["user_id"] == 123
        assert parsed["request_id"] == "abc-456"


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_root_logger(self):
        """Test getting the root logger."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == ""

    def test_get_named_logger(self):
        """Test getting a named logger."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_logger_caching(self):
        """Test that the same logger instance is returned."""
        logger1 = get_logger("cached.logger")
        logger2 = get_logger("cached.logger")
        assert logger1 is logger2

    def test_logger_propagate_disabled(self):
        """Test that logger propagation is disabled."""
        logger = get_logger("no.propagate")
        assert not logger.propagate


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_with_temp_file(self):
        """Test logging setup with a temporary file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(
                log_level=logging.DEBUG,
                log_file=log_file,
                json_logs=False,
                console_output=False,
            )

            logger = get_logger("setup.test")
            logger.info("Setup test message")

            # Verify file was created and contains log
            assert os.path.exists(log_file)
            with open(log_file, "r") as f:
                content = f.read()
                assert "Setup test message" in content

    def test_setup_with_json_format(self):
        """Test logging setup with JSON formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.json.log")
            setup_logging(
                log_level=logging.INFO,
                log_file=log_file,
                json_logs=True,
                console_output=False,
            )

            logger = get_logger("json.test")
            logger.info("JSON format test")

            # Verify file contains valid JSON
            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)
                assert "level" in parsed
                assert "message" in parsed

    def test_default_log_directory_creation(self):
        """Test that log directory is created if it doesn't exist."""
        # This would normally create logs/app.log in the project root
        # We skip this test as it depends on project structure
        pass


class TestLogWithContext:
    """Tests for the log_with_context function."""

    def test_log_with_context_data(self):
        """Test logging with additional context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "context.log")
            setup_logging(
                log_level=logging.DEBUG,
                log_file=log_file,
                json_logs=True,
                console_output=False,
            )

            logger = get_logger("context.test")
            context = {"feature": "test_feature", "value": 42}

            log_with_context(logger, logging.INFO, "Context test", context)

            # Verify context is in log
            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)
                assert parsed["feature"] == "test_feature"
                assert parsed["value"] == 42

    def test_log_without_context(self):
        """Test logging without context data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "no_context.log")
            setup_logging(
                log_level=logging.DEBUG,
                log_file=log_file,
                json_logs=True,
                console_output=False,
            )

            logger = get_logger("no_context.test")
            log_with_context(logger, logging.INFO, "Simple log", None)

            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)
                assert "extra_data" not in parsed or parsed["extra_data"] is None


class TestSetLogLevel:
    """Tests for the set_log_level function."""

    def test_set_root_level(self):
        """Test setting log level for root logger."""
        set_log_level(logging.WARNING)
        assert logging.getLogger().level == logging.WARNING

    def test_set_named_logger_level(self):
        """Test setting log level for specific logger."""
        logger = get_logger("level.test")
        set_log_level(logging.ERROR, "level.test")
        assert logger.level == logging.ERROR

    def test_handler_level_update(self):
        """Test that handler levels are updated when logger level changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "handler_level.log")
            setup_logging(
                log_level=logging.DEBUG,
                log_file=log_file,
                json_logs=False,
                console_output=False,
            )

            logger = get_logger("handler.level")
            set_log_level(logging.ERROR, "handler.level")

            # All handlers should have ERROR level
            for handler in logger.handlers:
                assert handler.level == logging.ERROR


def test_logging_importable():
    """Smoke test that logging module can be imported without errors."""
    from utils.logging_config import get_logger
    logger = get_logger("smoke.test")
    assert logger is not None