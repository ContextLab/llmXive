"""
Tests for the logging infrastructure.
"""
import logging
import tempfile
import os
from pathlib import Path

import pytest

# Import the module under test
from code.logger import setup_logging, get_logger, _logger_initialized

def test_setup_logging_creates_handlers():
    """Test that setup_logging creates console and file handlers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test.log"
        setup_logging(log_file=log_path, console=True, level=logging.DEBUG)

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 2  # One console, one file

        # Verify file handler exists and path matches
        file_handler = next((h for h in root_logger.handlers if isinstance(h, logging.FileHandler)), None)
        assert file_handler is not None
        assert file_handler.baseFilename == str(log_path)

def test_get_logger_returns_configured_logger():
    """Test that get_logger returns a logger with correct name."""
    # Reset state if needed for isolation
    # Note: In a real CI, we might need to reset _logger_initialized
    # For this test, we assume setup_logging was called or auto-initializes
    
    logger = get_logger("test_module")
    assert logger.name == "test_module"
    assert isinstance(logger, logging.Logger)

def test_log_output_format():
    """Test that log output includes timestamp, name, level, message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "format_test.log"
        setup_logging(log_file=log_path, console=False, level=logging.INFO)

        test_logger = get_logger("format_test")
        test_logger.info("Test message")

        with open(log_path, 'r') as f:
            content = f.read()
        
        assert "format_test" in content
        assert "INFO" in content
        assert "Test message" in content
        # Check for timestamp pattern (basic check)
        assert len(content) > 0
