"""
Unit tests for the logging infrastructure.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# We need to patch the _LOG_DIR to use a temporary directory for testing
# to avoid writing to the actual project data folder during unit tests.
import sys
from unittest.mock import patch

# Import the module
import code.utils.logging as logging_module

class TestLoggingInfrastructure:
    
    def test_get_logger_creates_instance(self):
        """Test that get_logger returns a valid Logger instance."""
        logger = logging_module.get_logger("test_unit")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_unit"

    def test_logger_has_handlers(self):
        """Test that the logger is configured with handlers."""
        logger = logging_module.get_logger("test_handlers")
        # Should have at least one handler (file or console)
        assert len(logger.handlers) > 0

    def test_logger_levels(self):
        """Test that log levels are set correctly."""
        logger = logging_module.get_logger("test_levels")
        assert logger.level == logging.DEBUG
        
        # Check handler levels
        has_file = False
        has_console = False
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                has_file = True
                assert handler.level == logging.DEBUG
            if isinstance(handler, logging.StreamHandler):
                has_console = True
                assert handler.level == logging.INFO
        
        # We expect at least one of them to exist
        assert has_file or has_console

    def test_log_output(self, tmp_path, caplog):
        """Test that logging actually writes messages."""
        # Create a temporary log directory
        temp_log_dir = tmp_path / "logs"
        temp_log_dir.mkdir()
        
        # Patch the _LOG_DIR in the module
        original_log_dir = logging_module._LOG_DIR
        logging_module._LOG_DIR = temp_log_dir
        
        # Force re-initialization by getting a new logger with a unique name
        # or clearing handlers. Here we just get a new one.
        test_logger = logging_module.get_logger("test_log_output_unique")
        
        # Ensure handlers are fresh for this test if possible, 
        # but since the module caches global state, we rely on the fact
        # that handlers are added if not present.
        
        # Log a message
        test_logger.info("Test info message")
        test_logger.debug("Test debug message")
        test_logger.warning("Test warning message")
        
        # Check that the file was created
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0, "Log file should be created in temp directory"
        
        # Read the content to verify
        log_content = log_files[0].read_text()
        assert "Test info message" in log_content
        assert "Test warning message" in log_content
        # Debug might be there depending on handler level
        
        # Restore original
        logging_module._LOG_DIR = original_log_dir

    def test_get_main_logger(self):
        """Test the convenience function."""
        logger = logging_module.get_main_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "osm_uhi"
