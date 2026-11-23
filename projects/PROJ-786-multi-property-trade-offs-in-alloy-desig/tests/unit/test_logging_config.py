"""
Unit tests for the logging configuration (T008).
"""

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_config import (
    configure_root_logger,
    get_logger,
    StructuredFormatter,
    ContextFilter,
    log_info_with_context,
    log_warning_with_context,
    log_error_with_context,
)

class TestStructuredFormatter:
    """Test the JSON structured log formatter."""

    def test_format_creates_valid_json(self):
        """Test that the formatter produces valid JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert json.loads(formatted) is not None

    def test_format_includes_timestamp(self):
        """Test that the formatted log includes a timestamp."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        log_dict = json.loads(formatted)
        assert "timestamp" in log_dict

    def test_format_includes_level(self):
        """Test that the formatted log includes the log level."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        log_dict = json.loads(formatted)
        assert log_dict["level"] == "WARNING"

class TestContextFilter:
    """Test the context filter for log records."""

    def test_filter_adds_context(self):
        """Test that the filter adds context to log records."""
        context = {"user_id": 123, "action": "login"}
        filter_obj = ContextFilter(context)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)
        assert hasattr(record, "context")
        assert record.context["user_id"] == 123

    def test_filter_merges_context(self):
        """Test that the filter merges existing context."""
        context = {"user_id": 123}
        filter_obj = ContextFilter(context)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.context = {"action": "login"}

        filter_obj.filter(record)
        assert record.context["user_id"] == 123
        assert record.context["action"] == "login"

class TestConfigureRootLogger:
    """Test the root logger configuration."""

    def test_configure_creates_handlers(self):
        """Test that configuration creates console and file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = configure_root_logger(log_file=log_file)

            assert len(logger.handlers) >= 2  # Console + File

    def test_configure_creates_log_file(self):
        """Test that configuration creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            configure_root_logger(log_file=log_file)

            logger = logging.getLogger()
            logger.info("Test message")

            # Force flush
            for handler in logger.handlers:
                handler.flush()

            assert os.path.exists(log_file)

    def test_configure_file_rotation(self):
        """Test that file handler has rotation configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            max_bytes = 1024
            backup_count = 3

            configure_root_logger(
                log_file=log_file, max_bytes=max_bytes, backup_count=backup_count
            )

            logger = logging.getLogger()
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    file_handler = handler
                    break

            assert file_handler is not None
            assert file_handler.maxBytes == max_bytes
            assert file_handler.backupCount == backup_count

class TestLogFunctions:
    """Test the convenience logging functions."""

    def test_log_info_with_context(self):
        """Test logging info with context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            configure_root_logger(log_file=log_file)
            logger = logging.getLogger("test_logger")

            log_info_with_context(
                logger, "Test info", {"key": "value"}, trace_id="test-123"
            )

            for handler in logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                log_line = f.readline()
                log_dict = json.loads(log_line)
                assert log_dict["level"] == "INFO"
                assert log_dict["message"] == "Test info"
                assert log_dict["context"]["key"] == "value"
                assert log_dict["trace_id"] == "test-123"

    def test_log_warning_with_context(self):
        """Test logging warning with context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            configure_root_logger(log_file=log_file)
            logger = logging.getLogger("test_logger")

            log_warning_with_context(
                logger, "Test warning", {"error": "timeout"}, trace_id="test-456"
            )

            for handler in logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                log_line = f.readline()
                log_dict = json.loads(log_line)
                assert log_dict["level"] == "WARNING"
                assert log_dict["message"] == "Test warning"
                assert log_dict["context"]["error"] == "timeout"
                assert log_dict["trace_id"] == "test-456"

    def test_log_error_with_context(self):
        """Test logging error with context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            configure_root_logger(log_file=log_file)
            logger = logging.getLogger("test_logger")

            log_error_with_context(
                logger, "Test error", {"code": 500}, trace_id="test-789"
            )

            for handler in logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                log_line = f.readline()
                log_dict = json.loads(log_line)
                assert log_dict["level"] == "ERROR"
                assert log_dict["message"] == "Test error"
                assert log_dict["context"]["code"] == 500
                assert log_dict["trace_id"] == "test-789"

class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_reuses_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2

    def test_get_logger_creates_different_instances(self):
        """Test that get_logger creates different instances for different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1 is not logger2