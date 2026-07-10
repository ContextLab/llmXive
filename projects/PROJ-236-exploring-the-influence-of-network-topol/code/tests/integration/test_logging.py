import logging
import os
import tempfile
from pathlib import Path
import pytest
from utils.logging import get_logger, log_message, get_log_file_path, LOG_DIR

class TestLoggingInfrastructure:
    """Integration tests for the base logging infrastructure."""

    def test_log_file_creation(self):
        """Verify that the log file is created upon first log write."""
        # Ensure the log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Clear any existing log file for a clean test
        log_path = get_log_file_path()
        if log_path.exists():
            log_path.unlink()
        
        # Trigger a log write
        log_message("Integration test initialization")
        
        # Verify the file exists
        assert log_path.exists(), "Log file was not created after logging a message."

    def test_message_appears_in_log_file(self):
        """Verify that a logged message actually appears in the designated log file."""
        test_message_content = f"Test message ID: {id(self)}"
        
        # Log the message
        log_message(test_message_content, level="info")
        
        # Read the log file
        log_path = get_log_file_path()
        assert log_path.exists(), "Log file does not exist."
        
        with open(log_path, "r") as f:
            log_content = f.read()
        
        # Verify the message is present
        assert test_message_content in log_content, (
            f"Test message '{test_message_content}' not found in log file."
        )

    def test_logger_levels(self):
        """Verify that different log levels are handled correctly."""
        logger = get_logger("level_test")
        
        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        log_path = get_log_file_path()
        with open(log_path, "r") as f:
            log_content = f.read()
        
        # Check that info, warning, and error are present
        # Note: Debug might be filtered out depending on config, but info+ should be there
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content
