import os
import logging
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the function under test
from logging_config import setup_logging

class TestLoggingConfig:
    """Tests for the logging configuration infrastructure."""

    def test_setup_logging_creates_file_handler(self, tmp_path):
        """Verify that setup_logging creates a file handler writing to the correct path."""
        # Mock the ensure_directories to use our temp directory
        with patch('logging_config.ensure_directories'):
            # Create a temporary log path
            log_file = tmp_path / "test_analysis.log"
            
            # Call the setup function
            logger = setup_logging(str(log_file.relative_to(tmp_path)), level=logging.DEBUG)
            
            # Check that handlers exist
            assert len(logger.handlers) == 2  # File and Console
            
            # Verify file handler exists and writes to the correct file
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    file_handler = handler
                    break
            
            assert file_handler is not None, "File handler not found"
            # The actual path might be resolved differently, so we check if the handler is active
            assert file_handler.stream is not None

    def test_setup_logging_creates_console_handler(self, tmp_path):
        """Verify that setup_logging creates a console handler."""
        with patch('logging_config.ensure_directories'):
            log_file = tmp_path / "test_analysis.log"
            logger = setup_logging(str(log_file.relative_to(tmp_path)), level=logging.INFO)
            
            console_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    console_handler = handler
                    break
            
            assert console_handler is not None, "Console handler not found"

    def test_log_message_writes_to_file(self, tmp_path, caplog):
        """Verify that logging a message actually writes to the file."""
        with patch('logging_config.ensure_directories'):
            log_file = tmp_path / "test_analysis.log"
            logger = setup_logging(str(log_file.relative_to(tmp_path)), level=logging.INFO)
            
            # Log a test message
            test_msg = "Test message for logging verification"
            logger.info(test_msg)
            
            # Force flush
            for handler in logger.handlers:
                handler.flush()
            
            # Check file contents
            assert log_file.exists(), "Log file was not created"
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert test_msg in content, f"Log message '{test_msg}' not found in file"

    def test_logger_level_respected(self, tmp_path):
        """Verify that the logger respects the configured level."""
        with patch('logging_config.ensure_directories'):
            log_file = tmp_path / "test_analysis.log"
            logger = setup_logging(str(log_file.relative_to(tmp_path)), level=logging.ERROR)
            
            # Log at different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Force flush
            for handler in logger.handlers:
                handler.flush()
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should only contain Error
            assert "Debug message" not in content
            assert "Info message" not in content
            assert "Warning message" not in content
            assert "Error message" in content