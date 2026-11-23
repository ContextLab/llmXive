import pytest
import logging
import sys
from pathlib import Path
from utils.logging_config import get_logger, fail_loudly, configure_data_fetch_logger

class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_reuses_instance(self):
        """Test that get_logger returns the same instance for same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2

class TestFailLoudly:
    """Tests for fail_loudly function."""

    def test_fail_loudly_with_message(self):
        """Test fail_loudly with just a message."""
        logger = get_logger("test_fail")
        
        with pytest.raises(SystemExit) as exc_info:
            fail_loudly(logger, "Test fatal error")
        
        assert exc_info.value.code == 1

    def test_fail_loudly_with_exception(self):
        """Test fail_loudly includes exception traceback."""
        logger = get_logger("test_fail")
        test_exception = ValueError("Test exception")
        
        with pytest.raises(SystemExit) as exc_info:
            fail_loudly(logger, "Test error", test_exception)
        
        assert exc_info.value.code == 1

    def test_fail_loudly_custom_exit_code(self):
        """Test fail_loudly with custom exit code."""
        logger = get_logger("test_fail")
        
        with pytest.raises(SystemExit) as exc_info:
            fail_loudly(logger, "Test error", error_code=2)
        
        assert exc_info.value.code == 2

class TestDataFetchLogger:
    """Tests for configure_data_fetch_logger function."""

    def test_configure_data_fetch_logger_returns_logger(self):
        """Test that configure_data_fetch_logger returns a valid logger."""
        logger = configure_data_fetch_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "data_fetch"

    def test_configure_data_fetch_logger_has_file_handler(self):
        """Test that data fetch logger has file handler."""
        logger = configure_data_fetch_logger()
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_configure_data_fetch_logger_has_console_handler(self):
        """Test that data fetch logger has console handler for errors."""
        logger = configure_data_fetch_logger()
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0
        # Console handler should be set to ERROR level
        assert console_handlers[0].level == logging.ERROR

    def test_configure_data_fetch_logger_custom_name(self):
        """Test configure_data_fetch_logger with custom name."""
        logger = configure_data_fetch_logger("custom_fetch")
        assert logger.name == "custom_fetch"
