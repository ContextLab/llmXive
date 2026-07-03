"""
Unit tests for the structured logging utilities.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import (
    setup_logger,
    get_logger,
    log_error,
    log_warning,
    log_info,
    log_debug,
    log_success,
    JsonFormatter,
)
from src.utils.config import get_path


class TestJsonFormatter:
    """Tests for the JSON formatter."""

    def test_format_returns_json_string(self):
        """Verify that the formatter returns a valid JSON string."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        assert isinstance(result, str)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"

    def test_format_includes_exception_info(self):
        """Verify that exception info is included when present."""
        formatter = JsonFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

            result = formatter.format(record)
            parsed = json.loads(result)
            
            assert "exception" in parsed
            assert parsed["exception"]["type"] == "ValueError"
            assert parsed["exception"]["message"] == "Test error"
            assert "traceback" in parsed["exception"]

    def test_format_includes_extra_data(self):
        """Verify that extra data is included when present."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value", "number": 42}

        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "data" in parsed
        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["number"] == 42


class TestSetupLogger:
    """Tests for logger setup functionality."""

    def test_setup_logger_creates_logger(self):
        """Verify that setup_logger returns a configured logger."""
        logger = setup_logger(name="test_setup")
        
        assert logger is not None
        assert logger.name == "test_setup"
        assert len(logger.handlers) > 0

    def test_setup_logger_with_file(self):
        """Verify that logger can write to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            
            logger = setup_logger(
                name="test_file",
                log_file=log_file,
                include_console=False,
            )
            
            logger.info("Test message")
            
            # Verify file exists and contains JSON
            assert os.path.exists(log_file)
            with open(log_file, "r") as f:
                content = f.read()
                parsed = json.loads(content.strip())
                assert parsed["message"] == "Test message"

    def test_setup_logger_multiple_calls_same_logger(self):
        """Verify that multiple calls return the same logger instance."""
        logger1 = setup_logger(name="test_single")
        logger2 = setup_logger(name="test_single")
        
        assert logger1 is logger2

    def test_setup_logger_different_names(self):
        """Verify that different names create different loggers."""
        logger1 = setup_logger(name="test_name1")
        logger2 = setup_logger(name="test_name2")
        
        assert logger1 is not logger2


class TestGetLogger:
    """Tests for get_logger functionality."""

    def test_get_logger_returns_configured_logger(self):
        """Verify that get_logger returns the configured logger."""
        setup_logger(name="test_get")
        logger = get_logger(name="test_get")
        
        assert logger is not None
        assert logger.name == "test_get"

    def test_get_logger_initializes_if_not_set(self):
        """Verify that get_logger initializes logger if not already set."""
        # Reset global logger
        import src.utils.logging as logging_module
        logging_module._logger = None
        
        logger = get_logger(name="test_init")
        
        assert logger is not None
        assert len(logger.handlers) > 0


class TestLogFunctions:
    """Tests for the convenience logging functions."""

    def test_log_info(self):
        """Verify that log_info logs at INFO level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_info.log")
            setup_logger(name="test_info", log_file=log_file, include_console=False)
            
            log_info("Test info message", logger_name="test_info")
            
            with open(log_file, "r") as f:
                content = json.loads(f.read().strip())
                assert content["level"] == "INFO"
                assert content["message"] == "Test info message"

    def test_log_warning(self):
        """Verify that log_warning logs at WARNING level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_warn.log")
            setup_logger(name="test_warn", log_file=log_file, include_console=False)
            
            log_warning("Test warning message", logger_name="test_warn")
            
            with open(log_file, "r") as f:
                content = json.loads(f.read().strip())
                assert content["level"] == "WARNING"
                assert content["message"] == "Test warning message"

    def test_log_error(self):
        """Verify that log_error logs at ERROR level with exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_error.log")
            setup_logger(name="test_error", log_file=log_file, include_console=False)
            
            try:
                raise ValueError("Test error")
            except ValueError as e:
                log_error("Error occurred", error=e, logger_name="test_error")
            
            with open(log_file, "r") as f:
                content = json.loads(f.read().strip())
                assert content["level"] == "ERROR"
                assert "exception" in content

    def test_log_success(self):
        """Verify that log_success logs at INFO level with success indicator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_success.log")
            setup_logger(name="test_success", log_file=log_file, include_console=False)
            
            log_success("Operation completed", logger_name="test_success")
            
            with open(log_file, "r") as f:
                content = json.loads(f.read().strip())
                assert content["level"] == "INFO"
                assert "[SUCCESS]" in content["message"]

    def test_log_with_extra_data(self):
        """Verify that extra data is included in log output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_extra.log")
            setup_logger(name="test_extra", log_file=log_file, include_console=False)
            
            extra_data = {"user_id": 123, "action": "test"}
            log_info("Action performed", extra=extra_data, logger_name="test_extra")
            
            with open(log_file, "r") as f:
                content = json.loads(f.read().strip())
                assert "data" in content
                assert content["data"]["user_id"] == 123
                assert content["data"]["action"] == "test"
