"""
Unit tests for the logging configuration utility.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.utils.logging_config import (
    setup_logging,
    get_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error_occurrence
)


class TestLoggingConfig:
    """Test suite for logging configuration."""

    def test_setup_logging_creates_log_file(self):
        """Verify that setup_logging creates the log file and directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_logs" / "pipeline.log"
            
            # Setup logging with custom path
            logger = setup_logging(str(log_path), log_level=logging.DEBUG)
            
            # Verify logger is configured
            assert isinstance(logger, logging.Logger)
            assert logger.level == logging.DEBUG
            
            # Verify log file was created
            assert log_path.exists()

    def test_get_logger_returns_configured_instance(self):
        """Verify that get_logger returns a properly configured logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_logs" / "pipeline.log"
            setup_logging(str(log_path))
            
            # Get a named logger
            logger = get_logger("test_module")
            
            # Verify it's the same root logger
            assert logger.name == "test_module"
            assert logger.level == logging.INFO  # Default level

    def test_log_pipeline_start_writes_message(self):
        """Verify that log_pipeline_start writes a start message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_logs" / "pipeline.log"
            setup_logging(str(log_path))
            
            # Log pipeline start
            log_pipeline_start("test_script.py")
            
            # Read log file and verify content
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "test_script.py" in content
            assert "starting" in content.lower()

    def test_log_pipeline_end_writes_message(self):
        """Verify that log_pipeline_end writes an end message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_logs" / "pipeline.log"
            setup_logging(str(log_path))
            
            # Log pipeline end (success)
            log_pipeline_end("test_script.py", success=True)
            
            # Read log file and verify content
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "test_script.py" in content
            assert "successfully" in content

    def test_log_error_occurrence_writes_error(self):
        """Verify that log_error_occurrence writes an error message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_logs" / "pipeline.log"
            setup_logging(str(log_path))
            
            # Create a test exception
            test_error = ValueError("Test error message")
            
            # Log the error
            log_error_occurrence("test_script.py", test_error)
            
            # Read log file and verify content
            with open(log_path, 'r') as f:
                content = f.read()
            
            assert "test_script.py" in content
            assert "error" in content.lower()
            assert "Test error message" in content

    def test_log_rotation_configuration(self):
        """Verify that log rotation is configured correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_logs" / "pipeline.log"
            max_bytes = 1024 * 1024  # 1 MB
            backup_count = 3
            
            # Setup logging with rotation parameters
            logger = setup_logging(
                str(log_path),
                max_bytes=max_bytes,
                backup_count=backup_count
            )
            
            # Verify handlers are configured
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    file_handler = handler
                    break
            
            assert file_handler is not None
            assert file_handler.maxBytes == max_bytes
            assert file_handler.backupCount == backup_count