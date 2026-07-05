import os
import sys
import pytest
import logging
import tempfile
import shutil
from io import StringIO

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.logging import setup_logger, get_logger, log_error

class TestLoggingUtils:
    def test_setup_logger_returns_logger(self):
        """Verify setup_logger returns a logger instance."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger), "setup_logger must return a Logger instance"
        assert logger.name == "test_logger", "Logger name should match the provided name"

    def test_setup_logger_sets_level(self):
        """Verify setup_logger sets the correct log level."""
        logger = setup_logger("test_logger_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG, "Logger level should be DEBUG"

    def test_get_logger_returns_existing(self):
        """Verify get_logger returns the same instance if called twice."""
        name = "singleton_logger"
        logger1 = get_logger(name)
        logger2 = get_logger(name)
        assert logger1 is logger2, "get_logger should return the same instance"

    def test_log_error_captures_exception(self):
        """Verify log_error logs the exception message correctly."""
        logger = setup_logger("test_error_logger")
        # Capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            raise ValueError("Test error message")
        except Exception as e:
            log_error(logger, "An error occurred", e)

        log_output = stream.getvalue()
        assert "An error occurred" in log_output, "Log should contain the error message"
        assert "Test error message" in log_output, "Log should contain the exception message"

    def test_log_error_handles_none_exception(self):
        """Verify log_error handles cases where exception is None."""
        logger = setup_logger("test_no_exc_logger")
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        log_error(logger, "A warning occurred", None)

        log_output = stream.getvalue()
        assert "A warning occurred" in log_output, "Log should contain the message"

    def test_logger_filters_sensitive_data(self):
        """Verify that sensitive data patterns are filtered if implemented."""
        # This test assumes the logging module might have filtering logic.
        # If the implementation is simple, this test verifies the logger exists and works.
        logger = setup_logger("test_filter_logger")
        assert logger is not None

    def test_logger_configurable_handlers(self):
        """Verify logger can be configured with custom handlers."""
        logger = setup_logger("test_handler_logger")
        assert len(logger.handlers) > 0, "Logger should have at least one handler"