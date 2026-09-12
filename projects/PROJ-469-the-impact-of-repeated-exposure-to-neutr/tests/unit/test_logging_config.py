"""
Unit tests for the logging configuration infrastructure.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from logging_config import (
    ColorFormatter,
    setup_logging,
    get_logger,
    log_exception,
    handle_critical_error,
    LOG_DIR,
    LOG_FILE,
)

class TestColorFormatter:
    """Tests for the ColorFormatter class."""

    def test_format_adds_color(self):
        """Test that format adds color codes to log level."""
        formatter = ColorFormatter("%(levelname)s - %(message)s")
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
        # Should contain ANSI color code for INFO (green)
        assert "\033[32m" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted

    def test_format_resets_color(self):
        """Test that format resets color at the end."""
        formatter = ColorFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        # Should contain reset code
        assert "\033[0m" in formatted

class TestSetupLogging:
    """Tests for the setup_logging function."""

    @patch("logging_config.ensure_dirs")
    @patch("logging_config.RotatingFileHandler")
    def test_setup_creates_log_directory(self, mock_handler, mock_ensure_dirs):
        """Test that setup_logging creates the log directory."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging(console=False, file=False)
            
            mock_ensure_dirs.assert_called_once_with([LOG_DIR])

    @patch("logging_config.ensure_dirs")
    def test_setup_creates_console_handler(self, mock_ensure_dirs):
        """Test that setup_logging creates a console handler when requested."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging(console=True, file=False)
            
            mock_logger.addHandler.assert_called()
            # Check that at least one handler was added
            assert mock_logger.addHandler.call_count >= 1

    @patch("logging_config.ensure_dirs")
    @patch("logging_config.RotatingFileHandler")
    def test_setup_creates_file_handler(self, mock_handler, mock_ensure_dirs):
        """Test that setup_logging creates a file handler when requested."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging(console=False, file=True)
            
            # RotatingFileHandler should be instantiated
            mock_handler.assert_called()

    @patch("logging_config.ensure_dirs")
    def test_setup_sets_log_level(self, mock_ensure_dirs):
        """Test that setup_logging sets the correct log level."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging(log_level="DEBUG", console=False, file=False)
            
            mock_logger.setLevel.assert_called_once_with(logging.DEBUG)

class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns a logger with the correct name."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_inherits_config(self):
        """Test that named logger inherits from root logger."""
        # Setup root logger first
        with patch("logging_config.ensure_dirs"):
            setup_logging(console=False, file=False)
        
        logger = get_logger("test_module")
        assert logger.level == logging.INFO  # Default level from setup

class TestLogException:
    """Tests for the log_exception function."""

    def test_log_exception_logs_traceback(self):
        """Test that log_exception logs the full traceback."""
        logger = MagicMock()
        
        try:
            raise ValueError("Test error")
        except:
            log_exception(logger, "Custom message")
        
        logger.error.assert_called()
        call_args = logger.error.call_args
        assert "Custom message" in call_args[0][0]
        # exc_info should be True to include traceback
        assert call_args[1].get("exc_info") is True

    def test_log_exception_handles_no_exception(self):
        """Test that log_exception handles case when no exception is active."""
        logger = MagicMock()
        
        # Not in an except block
        log_exception(logger, "No exception message")
        
        logger.error.assert_called()

class TestHandleCriticalError:
    """Tests for the handle_critical_error function."""

    @patch("logging_config.log_exception")
    @patch("logging_config.sys.exit")
    def test_handle_critical_error_exits(self, mock_exit, mock_log_exc):
        """Test that handle_critical_error exits the program."""
        logger = MagicMock()
        
        with pytest.raises(SystemExit):
            handle_critical_error(logger, "Critical error")
        
        mock_exit.assert_called_once_with(1)

    @patch("logging_config.log_exception")
    @patch("logging_config.sys.exit")
    def test_handle_critical_error_logs(self, mock_exit, mock_log_exc):
        """Test that handle_critical_error logs the error."""
        logger = MagicMock()
        
        with pytest.raises(SystemExit):
            handle_critical_error(logger, "Critical error")
        
        logger.critical.assert_called_once_with("Critical error")
        mock_log_exc.assert_called_once_with(logger)
