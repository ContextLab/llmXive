import logging
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import json

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.pipeline.logging_config import (
    JSONFormatter,
    get_logger,
    handle_error,
    log_with_context,
    time_execution,
    info,
    debug,
    warning,
    error,
    critical,
)


class TestLoggingConfig(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_logger = get_logger("test_logging")
        # Remove existing handlers to avoid duplicates in tests
        self.test_logger.handlers = []

    def test_json_formatter_formats_as_json(self):
        """Test that JSONFormatter outputs valid JSON."""
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

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["message"], "Test message")
        self.assertIn("timestamp", parsed)
        self.assertIn("logger", parsed)

    def test_json_formatter_includes_exception(self):
        """Test that JSONFormatter includes exception info when present."""
        formatter = JSONFormatter()

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

            formatted = formatter.format(record)
            parsed = json.loads(formatted)

            self.assertIn("exception", parsed)
            self.assertEqual(parsed["exception"]["type"], "ValueError")
            self.assertEqual(parsed["exception"]["message"], "Test error")
            self.assertIsNotNone(parsed["exception"]["traceback"])

    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a properly configured logger."""
        logger = get_logger("test_config")
        # Remove handlers to avoid side effects
        logger.handlers = []

        self.assertEqual(logger.name, "test_config")
        self.assertGreaterEqual(logger.level, logging.INFO)

    def test_handle_error_logs_and_raises(self):
        """Test that handle_error logs the error and re-raises it."""
        logger = get_logger("test_error")
        logger.handlers = []

        # Add a mock handler to capture logs
        mock_handler = MagicMock()
        logger.addHandler(mock_handler)

        test_error = ValueError("Test error message")

        with self.assertRaises(ValueError):
            handle_error(logger, test_error, {"key": "value"}, raise_error=True)

        # Verify error was logged
        self.assertTrue(mock_handler.error.called)

    def test_handle_error_logs_without_raising(self):
        """Test that handle_error logs without raising when raise_error=False."""
        logger = get_logger("test_no_raise")
        logger.handlers = []

        mock_handler = MagicMock()
        logger.addHandler(mock_handler)

        test_error = ValueError("Test error")

        # Should not raise
        handle_error(logger, test_error, raise_error=False)

        self.assertTrue(mock_handler.error.called)

    def test_log_with_context_includes_context(self):
        """Test that log_with_context includes context in the log."""
        logger = get_logger("test_context")
        logger.handlers = []

        mock_handler = MagicMock()
        logger.addHandler(mock_handler)

        log_with_context(logger, logging.INFO, "Test message", {"user": "test"})

        # Verify the log call included context
        call_args = mock_handler.emit.call_args
        self.assertIsNotNone(call_args)

    def test_time_execution_decorator_logs_duration(self):
        """Test that time_execution decorator logs execution time."""
        logger = get_logger("test_timer")
        logger.handlers = []

        mock_handler = MagicMock()
        logger.addHandler(mock_handler)

        @time_execution(logger, logging.INFO)
        def test_func():
            time.sleep(0.01)
            return "result"

        result = test_func()
        self.assertEqual(result, "result")

        # Verify log was called with timing info
        self.assertTrue(mock_handler.info.called)

    def test_time_execution_decorator_handles_exceptions(self):
        """Test that time_execution handles and logs exceptions."""
        logger = get_logger("test_timer_err")
        logger.handlers = []

        mock_handler = MagicMock()
        logger.addHandler(mock_handler)

        @time_execution(logger, logging.INFO)
        def failing_func():
            raise ValueError("Expected error")

        with self.assertRaises(ValueError):
            failing_func()

        # Verify error was logged
        self.assertTrue(mock_handler.error.called)

    def test_convenience_functions(self):
        """Test that convenience functions work correctly."""
        logger = get_logger("test_convenience")
        logger.handlers = []

        mock_handler = MagicMock()
        logger.addHandler(mock_handler)

        info("Info message")
        debug("Debug message")
        warning("Warning message")
        error("Error message")
        critical("Critical message")

        # Verify all levels were called
        self.assertTrue(mock_handler.info.called)
        self.assertTrue(mock_handler.debug.called)
        self.assertTrue(mock_handler.warning.called)
        self.assertTrue(mock_handler.error.called)
        self.assertTrue(mock_handler.critical.called)
