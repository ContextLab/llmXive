import os
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to ensure the logs directory exists for the test to run without errors
# but we can test the logger configuration in isolation.
from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event

class TestLoggingConfig:
    def test_get_logger_returns_valid_instance(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_logger_1")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_1"
        assert len(logger.handlers) > 0

    def test_log_exclusion_reason_formats_correctly(self, caplog):
        """Test that log_exclusion_reason logs with the correct format."""
        logger = get_logger("test_logger_2")
        # We need to capture the log output. Since we use a file handler and console,
        # we can temporarily set the level and check the handler's output or use caplog
        # if we configure caplog to capture the logger.
        
        # Reset handlers for clean test if necessary, but caplog usually works with propagation
        # However, our logger adds handlers directly. Let's verify the message content.
        
        # We will verify that the function calls logger.warning with the expected string.
        # Since we can't easily inspect the RotatingFileHandler content in a unit test without file I/O,
        # we will check that the function executes without error and logs a warning.
        
        # To make it testable with caplog, we need to ensure the logger propagates or we inspect the handler.
        # Let's just verify the function call works and logs at the correct level.
        
        with caplog.at_level(logging.WARNING, logger="test_logger_2"):
            log_exclusion_reason("MISSING_DATA", "material_123", "Ionic radius missing")
            assert "EXCLUSION" in caplog.text
            assert "Category: MISSING_DATA" in caplog.text
            assert "ID: material_123" in caplog.text
            assert "Reason: Ionic radius missing" in caplog.text

    def test_log_pipeline_event_formats_correctly(self, caplog):
        """Test that log_pipeline_event logs with the correct format."""
        logger = get_logger("test_logger_3")
        
        with caplog.at_level(logging.INFO, logger="test_logger_3"):
            log_pipeline_event("DATA_LOADED", "features.csv loaded successfully")
            assert "EVENT" in caplog.text
            assert "Type: DATA_LOADED" in caplog.text
            assert "Details: features.csv loaded successfully" in caplog.text

    def test_log_pipeline_event_supports_error_level(self, caplog):
        """Test that log_pipeline_event can log errors."""
        logger = get_logger("test_logger_4")
        
        with caplog.at_level(logging.ERROR, logger="test_logger_4"):
            log_pipeline_event("ERROR", "API rate limit exceeded", level=logging.ERROR)
            assert "EVENT" in caplog.text
            assert "Type: ERROR" in caplog.text
            assert "Details: API rate limit exceeded" in caplog.text
            assert "ERROR" in caplog.text # Check log level indicator
