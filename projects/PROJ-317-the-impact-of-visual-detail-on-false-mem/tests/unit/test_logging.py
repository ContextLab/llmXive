"""
Unit tests for the logging infrastructure.
"""

import os
import tempfile
from pathlib import Path
import pytest

# We need to mock the project root logic or ensure the test environment
# can find the code directory. Since we are running tests from the repo root,
# we assume code/utils/logging.py is accessible.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import (
    get_logger,
    get_log_file_path,
    get_error_log_file_path,
    _LOGS_DIR,
    _configure_logging,
    _configured
)


class TestLoggingInfrastructure:
    """Tests for the logging module."""

    def test_logger_initialization(self):
        """Test that a logger can be retrieved and is configured."""
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "llmXive.test_module"
        # Verify it has handlers
        assert len(logger.handlers) == 0  # Child loggers inherit handlers from parent, usually empty list directly
        parent = logger.parent
        assert parent is not None
        assert len(parent.handlers) > 0

    def test_root_logger_handlers(self):
        """Test that the root logger has the expected handlers."""
        logger = get_logger()
        # Should have at least console, file, and error file handlers
        assert len(logger.handlers) >= 3

    def test_log_file_exists_after_use(self):
        """Test that logging to the logger creates the file."""
        logger = get_logger("test_file_creation")
        logger.info("Test message for file creation")

        log_path = get_log_file_path()
        assert log_path.exists(), f"Log file {log_path} was not created."

    def test_error_log_file_exists_after_use(self):
        """Test that logging an error creates the error file."""
        logger = get_logger("test_error_creation")
        logger.error("Test error message")

        error_path = get_error_log_file_path()
        assert error_path.exists(), f"Error log file {error_path} was not created."

    def test_get_manipulation_error_log_path(self):
        """Test that the manipulation error log path is valid."""
        from utils.logging import get_manipulation_error_log_path
        path = get_manipulation_error_log_path()
        assert path.suffix == ".log"
        assert "manipulation_errors" in path.name

    def test_logger_propagation(self):
        """Test that child loggers propagate to parent."""
        logger = get_logger("test_propagation")
        assert logger.propagate is True