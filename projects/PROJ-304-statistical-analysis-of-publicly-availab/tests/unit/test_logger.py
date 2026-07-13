import pytest
import sys
import os

# Ensure the code directory is in the path for imports if running via pytest
# though the runner usually handles this.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from logger import test_log_format, get_logger, FORMAT_STRING


class TestLoggerFormat:
    """
    Tests for the logger configuration and format string verification.
    """

    def test_log_format_function_returns_true(self):
        """
        Verifies that the test_log_format function returns True
        when the format string is correctly applied.
        """
        result = test_log_format()
        assert result is True, "test_log_format should return True for correct format"

    def test_format_string_constant(self):
        """
        Verifies the FORMAT_STRING constant matches the specification exactly.
        """
        expected = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert FORMAT_STRING == expected, f"FORMAT_STRING mismatch. Expected: {expected}, Got: {FORMAT_STRING}"

    def test_logger_creation(self):
        """
        Verifies that get_logger returns a valid logging.Logger instance.
        """
        logger = get_logger("test_unit_creation")
        assert logger is not None
        assert logger.name == "test_unit_creation"
        assert len(logger.handlers) > 0, "Logger should have handlers configured"
        
        # Verify at least one handler is a RotatingFileHandler
        from logging.handlers import RotatingFileHandler
        has_rotating = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
        assert has_rotating, "Logger must have a RotatingFileHandler"