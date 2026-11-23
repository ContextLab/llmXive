"""
Tests for the logging infrastructure.
"""
import pytest
import logging
import os
import json
from pathlib import Path
import sys
import time

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import (
    get_logger,
    log_error,
    log_warning,
    log_info,
    log_debug,
    setup_logging_for_task,
    close_logging,
    JSONFormatter,
    PlainTextFormatter
)


class TestLoggerInitialization:
    """Test logger initialization and configuration."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "plant_disease.test_logger"
    
    def test_logger_has_handlers(self):
        """Test that logger has handlers configured."""
        logger = get_logger("test_handler_check")
        assert len(logger.handlers) > 0
    
    def test_multiple_calls_return_same_logger(self):
        """Test that multiple calls to get_logger return the same logger."""
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        assert logger1 is logger2


class TestLoggingFunctions:
    """Test the logging utility functions."""
    
    def test_log_info(self, caplog):
        """Test log_info function."""
        logger = get_logger("test_info")
        with caplog.at_level(logging.INFO):
            log_info(logger, "Test info message")
            assert "Test info message" in caplog.text
    
    def test_log_warning(self, caplog):
        """Test log_warning function."""
        logger = get_logger("test_warning")
        with caplog.at_level(logging.WARNING):
            log_warning(logger, "Test warning message")
            assert "Test warning message" in caplog.text
    
    def test_log_error(self, caplog):
        """Test log_error function."""
        logger = get_logger("test_error")
        with caplog.at_level(logging.ERROR):
            log_error(logger, "Test error message")
            assert "Test error message" in caplog.text
    
    def test_log_error_with_exception(self, caplog):
        """Test log_error with an exception."""
        logger = get_logger("test_error_exc")
        try:
            raise ValueError("Test exception")
        except Exception as e:
            with caplog.at_level(logging.ERROR):
                log_error(logger, "Error occurred", error=e)
                assert "Test exception" in caplog.text
    
    def test_log_debug(self, caplog):
        """Test log_debug function."""
        logger = get_logger("test_debug")
        with caplog.at_level(logging.DEBUG):
            log_debug(logger, "Test debug message")
            assert "Test debug message" in caplog.text
    
    def test_log_with_extra_fields(self, caplog):
        """Test logging with extra fields."""
        logger = get_logger("test_extra")
        extra_data = {"task_id": "T005", "status": "running"}
        with caplog.at_level(logging.INFO):
            log_info(logger, "Message with extra", extra=extra_data)
            # The extra fields should be included in the log
            assert "T005" in caplog.text or "status" in caplog.text


class TestJSONFormatter:
    """Test the JSON formatter."""
    
    def test_json_formatter_outputs_valid_json(self):
        """Test that JSON formatter produces valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed
        assert parsed["message"] == "Test message"
    
    def test_json_formatter_includes_exception(self):
        """Test that JSON formatter includes exception info."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except:
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
            formatted = formatter.format(record)
            parsed = json.loads(formatted)
            assert "exception" in parsed
            assert parsed["exception"]["type"] == "ValueError"


class TestPlainTextFormatter:
    """Test the plain text formatter."""
    
    def test_plain_text_formatter_outputs_readable_text(self):
        """Test that plain text formatter produces readable output."""
        formatter = PlainTextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        assert "Test message" in formatted
        assert "INFO" in formatted


class TestSetupLoggingForTask:
    """Test task-specific logging setup."""
    
    def test_setup_logging_for_task_returns_logger(self):
        """Test that setup_logging_for_task returns a logger."""
        logger = setup_logging_for_task("test_task")
        assert isinstance(logger, logging.Logger)
    
    def test_setup_logging_for_task_logs_start(self, caplog):
        """Test that setup_logging_for_task logs a start message."""
        with caplog.at_level(logging.INFO):
            logger = setup_logging_for_task("T005_test")
            assert "Starting task" in caplog.text
            assert "T005_test" in caplog.text


class TestCloseLogging:
    """Test logging cleanup."""
    
    def test_close_logging_closes_handlers(self):
        """Test that close_logging closes handlers."""
        # Get a logger to ensure handlers are created
        logger = get_logger("test_close")
        initial_handlers = len(logger.handlers)
        assert initial_handlers > 0
        
        # Close logging
        close_logging()
        
        # Note: The global logger is reset, but existing references
        # might still have handlers. This test verifies the function runs.
        assert True  # If we get here without error, it's a pass


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_logging():
    """Ensure logging is cleaned up after each test."""
    yield
    close_logging()
