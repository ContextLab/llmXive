import os
import sys
import logging
import tempfile
import json
from pathlib import Path
import pytest

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logger import (
    setup_logger, 
    get_pipeline_logger, 
    log_error, 
    log_warning, 
    log_info, 
    log_debug,
    PipelineError,
    DataFetchError,
    handle_error,
    validate_not_null,
    validate_positive
)
from config import get_config

class TestLoggerInfrastructure:
    """Tests for the logging infrastructure and error handling utilities."""

    def test_setup_logger_creates_instance(self):
        """Test that setup_logger creates and returns a logger instance."""
        logger = setup_logger("test_logger_1")
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger_1"

    def test_get_pipeline_logger_reuses_instance(self):
        """Test that get_pipeline_logger returns the same instance if already initialized."""
        # First call initializes
        logger1 = get_pipeline_logger("test_shared")
        # Second call should return the same
        logger2 = get_pipeline_logger("test_shared")
        assert logger1 is logger2

    def test_log_info_writes_message(self, caplog):
        """Test that log_info writes an info message."""
        # Temporarily set level to INFO to capture logs
        logger = setup_logger("test_info", level=logging.INFO)
        
        with caplog.at_level(logging.INFO):
            log_info("Test info message")
        
        assert "Test info message" in caplog.text
        assert "INFO" in caplog.text

    def test_log_warning_writes_message(self, caplog):
        """Test that log_warning writes a warning message."""
        logger = setup_logger("test_warning", level=logging.WARNING)
        
        with caplog.at_level(logging.WARNING):
            log_warning("Test warning message")
        
        assert "Test warning message" in caplog.text
        assert "WARNING" in caplog.text

    def test_log_error_writes_exception(self, caplog):
        """Test that log_error writes exception details."""
        logger = setup_logger("test_error", level=logging.ERROR)
        test_exception = ValueError("Test error value")
        
        with caplog.at_level(logging.ERROR):
            log_error(test_exception, "Test Context")
        
        assert "Test Context" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test error value" in caplog.text

    def test_log_file_creation(self):
        """Test that log_file parameter creates a file with entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_pipeline.log"
            logger = setup_logger("test_file_log", log_file=str(log_path), level=logging.INFO)
            
            log_info("File log test message")
            
            assert log_path.exists()
            content = log_path.read_text()
            assert "File log test message" in content
            assert "INFO" in content

    def test_pipeline_error_custom_exception(self):
        """Test that PipelineError stores message and details."""
        details = {"key": "value", "code": 404}
        error = PipelineError("Pipeline failed", details)
        
        assert error.message == "Pipeline failed"
        assert error.details == details
        assert "Pipeline failed" in str(error)

    def test_data_fetch_error_subclass(self):
        """Test that DataFetchError is a subclass of PipelineError."""
        error = DataFetchError("Fetch failed")
        assert isinstance(error, PipelineError)
        assert error.message == "Fetch failed"

    def test_handle_error_logs_and_raises(self):
        """Test that handle_error logs the error and re-raises it."""
        logger = setup_logger("test_handle", level=logging.ERROR)
        test_exception = RuntimeError("Handle test")
        
        with pytest.raises(RuntimeError) as exc_info:
            handle_error(test_exception, "Handle Context")
        
        assert exc_info.value is test_exception

    def test_validate_not_null_pass(self):
        """Test validate_not_null with valid value."""
        result = validate_not_null("valid", "field_name")
        assert result == "valid"

    def test_validate_not_null_fail(self):
        """Test validate_not_null with None raises ValueError."""
        with pytest.raises(ValueError, match="cannot be None"):
            validate_not_null(None, "field_name")

    def test_validate_positive_pass(self):
        """Test validate_positive with positive value."""
        result = validate_positive(10.5, "value_field")
        assert result == 10.5

    def test_validate_positive_fail_zero(self):
        """Test validate_positive with zero raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive(0, "value_field")

    def test_validate_positive_fail_negative(self):
        """Test validate_positive with negative value raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive(-5, "value_field")

    def test_validate_positive_fail_string(self):
        """Test validate_positive with non-numeric value raises ValueError."""
        with pytest.raises(ValueError, match="must be numeric"):
            validate_positive("not a number", "value_field")

    def test_logger_write_and_read_entry(self):
        """
        Unit test for T005d: Write and read a log entry.
        Verifies that the logger actually writes to a file and the entry can be retrieved.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "write_read_test.log"
            test_message = "T005d verification entry"
            
            # Setup logger with file output
            logger = setup_logger(
                "write_read_test",
                log_file=str(log_path),
                level=logging.INFO
            )
            
            # Write a log entry
            log_info(test_message)
            
            # Verify file exists
            assert log_path.exists(), "Log file was not created"
            
            # Read the file content
            content = log_path.read_text()
            
            # Verify the specific message is present
            assert test_message in content, f"Message '{test_message}' not found in log file"
            
            # Verify standard log format components are present
            assert "INFO" in content, "Log level INFO not found"
            assert "write_read_test" in content, "Logger name not found"
            
            # Verify we can parse the line (basic structural check)
            lines = content.strip().split('\n')
            assert len(lines) > 0, "Log file is empty"
            
            # Check that the line contains the message and level
            last_line = lines[-1]
            assert test_message in last_line
            assert "INFO" in last_line