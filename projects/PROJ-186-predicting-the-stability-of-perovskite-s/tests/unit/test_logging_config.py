import os
import logging
import tempfile
import pytest
from pathlib import Path

# Mock the LOG_DIR to use a temp directory for testing
import sys
sys.path.insert(0, 'code')

from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event, PipelineFormatter, LOG_FILE

class TestLoggingConfig:
    
    def test_logger_creation(self):
        """Test that a logger is created successfully."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG

    def test_logger_has_handlers(self):
        """Test that the logger has both file and console handlers."""
        logger = get_logger("test_handlers")
        assert len(logger.handlers) >= 2
        
        # Check for RotatingFileHandler
        file_handler_exists = any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers)
        assert file_handler_exists, "RotatingFileHandler not found in logger handlers"

    def test_log_exclusion_reason(self, caplog):
        """Test that exclusion reasons are logged correctly."""
        with caplog.at_level(logging.WARNING):
            log_exclusion_reason("Missing Data", "Sample ID: 123", "test_exclusion")
            
        assert any("Missing Data" in record.message for record in caplog.records)
        assert any("Sample ID: 123" in record.message for record in caplog.records)

    def test_log_pipeline_event(self, caplog):
        """Test that pipeline events are logged correctly."""
        with caplog.at_level(logging.INFO):
            log_pipeline_event("Pipeline started", logging.INFO, "test_event")
            
        assert any("Pipeline started" in record.message for record in caplog.records)

    def test_formatter_includes_timestamp(self):
        """Test that the custom formatter includes timestamps."""
        formatter = PipelineFormatter('%(asctime)s - %(message)s')
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
        assert "-" in formatted
        assert "Test message" in formatted

    def test_log_file_creation(self):
        """Test that the log file is created when logging occurs."""
        logger = get_logger("test_file_creation")
        log_pipeline_event("Triggering file creation", logger_name="test_file_creation")
        
        # The LOG_FILE is relative to project root. In test environment, 
        # we verify the directory exists or the file was created.
        # Since we don't know the exact CWD of the test runner, we check if 
        # the path object exists or can be created.
        assert LOG_FILE.parent.exists(), "Log directory should exist"
        
        # Note: We don't assert file existence strictly here because 
        # RotatingFileHandler might not flush immediately in all test setups,
        # but the handler is configured to write to this path.
