"""
Unit tests for the structured logging infrastructure (T009).

These tests verify:
1. The logger initializes correctly.
2. Log messages contain the required structure (Timestamp, Level, TaskID, Component).
3. Error codes (ERR-###) are correctly formatted and included when provided.
4. The error code registry contains valid definitions.
"""
import logging
import sys
import io
import re
import pytest
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming tests are run from the project root or code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils.logger import (
    get_default_logger,
    AuditLogger,
    get_error_message,
    log_error,
    log_info,
    log_warning,
    ERROR_CODES,
)


class TestErrorCodes:
    """Tests for the error code registry."""

    def test_error_codes_exist(self):
        """Verify that the error code registry is not empty."""
        assert len(ERROR_CODES) > 0, "ERROR_CODES registry must not be empty."

    def test_error_code_format(self):
        """Verify that all error codes follow the ERR-### format."""
        pattern = re.compile(r"^ERR-\d{3}$")
        for code in ERROR_CODES.keys():
            assert pattern.match(code), f"Error code '{code}' does not match ERR-### format."

    def test_get_error_message_valid(self):
        """Verify that get_error_message returns the correct description."""
        msg = get_error_message("ERR-001")
        assert "Missing required field" in msg, f"Unexpected message for ERR-001: {msg}"

    def test_get_error_message_invalid(self):
        """Verify behavior for unknown error codes."""
        msg = get_error_message("ERR-999")
        assert "Unknown error code" in msg

class TestAuditLogger:
    """Tests for the AuditLogger class and formatting."""

    def get_handler_output(self, logger: AuditLogger, message: str, level=logging.INFO) -> str:
        """Helper to capture log output to a string."""
        # Create a string buffer to capture logs
        string_io = io.StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setLevel(logging.DEBUG)
        # Use a simple formatter to check raw output, but the adapter formats the message
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.DEBUG)

        if level == logging.ERROR:
            logger.error(message)
        elif level == logging.WARNING:
            logger.warning(message)
        else:
            logger.info(message)

        logger.logger.removeHandler(handler)
        return string_io.getvalue().strip()

    def test_logger_initialization(self):
        """Verify logger can be created with task_id and component."""
        logger = get_default_logger(name="test_logger", task_id="T009", log_file=None)
        assert logger is not None
        assert logger.extra["task_id"] == "T009"
        assert logger.extra["component"] == "unknown"

    def test_log_contains_task_id(self):
        """Verify that log messages contain the Task ID."""
        logger = get_default_logger(name="test_task_id", task_id="T009", log_file=None)
        output = self.get_handler_output(logger, "Test message")
        assert "[T009]" in output, f"Task ID not found in log output: {output}"

    def test_log_contains_component(self):
        """Verify that log messages contain the component name."""
        logger = get_default_logger(name="test_component", task_id="T009", log_file=None)
        # Override component via log_error or similar if needed, but default is 'unknown'
        # Let's test the default
        output = self.get_handler_output(logger, "Test message")
        assert "[unknown]" in output, f"Component not found in log output: {output}"

    def test_log_contains_error_code(self):
        """Verify that log messages contain the error code when provided."""
        logger = get_default_logger(name="test_err", task_id="T009", log_file=None)
        log_error(logger, "ERR-001", "Test error", component="test_comp")
        # We need to capture the output again specifically for the error logger created inside log_error
        # The log_error function creates a new AuditLogger. Let's test the formatting directly.
        
        # Create a logger with error code
        base_logger = logging.getLogger("test_direct")
        base_logger.handlers = [] # Clear
        string_io = io.StringIO()
        handler = logging.StreamHandler(string_io)
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.DEBUG)

        err_logger = AuditLogger(base_logger, extra={"component": "test"}, error_code="ERR-002")
        err_logger.error("Test error message")

        output = string_io.getvalue().strip()
        assert "[ERR-002]" in output, f"Error code not found in log output: {output}"
        assert "Test error message" in output

    def test_log_contains_timestamp(self):
        """Verify that log messages contain a timestamp."""
        logger = get_default_logger(name="test_time", task_id="T009", log_file=None)
        output = self.get_handler_output(logger, "Test message")
        # Timestamp format is ISO 8601 (e.g., 2026-06-27T19:32:53.038071)
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", output), f"Timestamp not found in: {output}"

    def test_log_contains_level(self):
        """Verify that log messages contain the log level."""
        logger = get_default_logger(name="test_level", task_id="T009", log_file=None)
        
        # Test INFO
        output_info = self.get_handler_output(logger, "Info message", logging.INFO)
        assert "[INFO]" in output_info, f"INFO level not found: {output_info}"

        # Test ERROR
        # We need to re-attach handler for the error test or use a fresh one
        string_io = io.StringIO()
        handler = logging.StreamHandler(string_io)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.DEBUG)
        logger.error("Error message")
        output_error = string_io.getvalue().strip()
        logger.logger.removeHandler(handler)
        
        assert "[ERROR]" in output_error, f"ERROR level not found: {output_error}"

class TestLogHelpers:
    """Tests for the helper logging functions."""

    def test_log_error_format(self):
        """Verify log_error produces correctly formatted output."""
        logger = get_default_logger(name="test_helper", task_id="T009", log_file=None)
        
        string_io = io.StringIO()
        handler = logging.StreamHandler(string_io)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.DEBUG)

        log_error(logger, "ERR-003", "Sample size mismatch", component="validator")
        
        output = string_io.getvalue().strip()
        logger.logger.removeHandler(handler)

        assert "[ERR-003]" in output
        assert "[validator]" in output
        assert "Sample size mismatch" in output

    def test_log_warning_format(self):
        """Verify log_warning produces correctly formatted output."""
        logger = get_default_logger(name="test_warn", task_id="T009", log_file=None)
        
        string_io = io.StringIO()
        handler = logging.StreamHandler(string_io)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.DEBUG)

        log_warning(logger, "Potential issue detected", component="fetcher")
        
        output = string_io.getvalue().strip()
        logger.logger.removeHandler(handler)

        assert "[WARNING]" in output
        assert "[fetcher]" in output
        assert "Potential issue detected" in output

    def test_log_info_format(self):
        """Verify log_info produces correctly formatted output."""
        logger = get_default_logger(name="test_info", task_id="T009", log_file=None)
        
        string_io = io.StringIO()
        handler = logging.StreamHandler(string_io)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.DEBUG)

        log_info(logger, "Processing started", component="pipeline")
        
        output = string_io.getvalue().strip()
        logger.logger.removeHandler(handler)

        assert "[INFO]" in output
        assert "[pipeline]" in output
        assert "Processing started" in output

if __name__ == "__main__":
    pytest.main([__file__, "-v"])