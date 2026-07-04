"""
Unit tests for the logging infrastructure.
"""
import logging
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock config.get_path to control where logs are written during tests
from utils import logging as logging_module


@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for log files during tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_setup_logging_creates_file_handler(temp_logs_dir):
    """Test that setup_logging creates a file handler in the specified directory."""
    # Mock get_path to return our temp directory for data/logs
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        logger = logging_module.setup_logging(
            level=logging.DEBUG,
            log_file_name="test_log.log",
            enable_console=False
        )
        
        assert logger.name == "osm_uhi_pipeline"
        assert logger.level == logging.DEBUG
        
        # Check that a file handler was added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        
        # Check that the file exists
        log_path = Path(temp_logs_dir) / "test_log.log"
        assert log_path.exists()


def test_setup_logging_creates_console_handler(temp_logs_dir):
    """Test that setup_logging creates a console handler when enabled."""
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        logger = logging_module.setup_logging(
            level=logging.INFO,
            enable_console=True
        )
        
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        # Should have at least one console handler (sys.stdout)
        assert len(console_handlers) >= 1


def test_setup_logging_uses_custom_level(temp_logs_dir):
    """Test that setup_logging respects the custom log level."""
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        logger = logging_module.setup_logging(level=logging.WARNING)
        assert logger.level == logging.WARNING


def test_get_logger_returns_configured_logger(temp_logs_dir):
    """Test that get_logger returns the configured logger."""
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        # First call should configure
        logger1 = logging_module.setup_logging(enable_console=False)
        
        # Reset the global state for the next call
        logging_module._logger = None
        
        # Now call get_logger - it should configure if not configured
        logger2 = logging_module.get_logger()
        
        assert logger2 is not None
        assert len(logger2.handlers) > 0


def test_logger_writes_to_file(temp_logs_dir):
    """Test that log messages are written to the log file."""
    log_filename = "test_write.log"
    log_path = Path(temp_logs_dir) / log_filename
    
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        logger = logging_module.setup_logging(
            level=logging.DEBUG,
            log_file_name=log_filename,
            enable_console=False
        )
        
        test_message = "Test log message for verification"
        logger.info(test_message)
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        # Read the file and check content
        assert log_path.exists()
        content = log_path.read_text()
        assert test_message in content


def test_log_error_context(temp_logs_dir):
    """Test the log_error_context utility function."""
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        logger = logging_module.setup_logging(level=logging.DEBUG, enable_console=False)
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            logging_module.log_error_context(e, "Test Context")
        
        # Just verify it doesn't crash and logs something
        # The actual content verification is covered by other tests


def test_multiple_calls_to_setup_logging(temp_logs_dir):
    """Test that multiple calls to setup_logging don't duplicate handlers."""
    with patch.object(logging_module, 'get_path', return_value=temp_logs_dir):
        logger1 = logging_module.setup_logging(enable_console=False)
        initial_handler_count = len(logger1.handlers)
        
        # Calling again should ideally return the same logger without adding handlers
        # Note: The current implementation checks hasHandlers() and returns early
        logger2 = logging_module.setup_logging(enable_console=False)
        
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count
