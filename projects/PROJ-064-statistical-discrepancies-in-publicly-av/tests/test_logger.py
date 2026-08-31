"""
Unit tests for the logging infrastructure.
"""
import pytest
import logging
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import modules under test
from logger import (
    setup_logging,
    get_logger,
    JSONFormatter,
    log_with_context,
    LOG_LEVELS,
    _CONFIGURED,
    _LOGGERS
)
from exceptions import DiscrepancyError

class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_defaults(self):
        """Test default logging setup."""
        # Reset state
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging()
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0  # At least console handler
    
    def test_setup_logging_custom_level(self):
        """Test logging setup with custom log level."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging(log_level="DEBUG")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_invalid_level(self):
        """Test that invalid log level raises ValueError."""
        import logger
        logger._CONFIGURED = False
        
        with pytest.raises(ValueError):
            setup_logging(log_level="INVALID")
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file handler."""
        import logger
        logger._CONFIGURED = False
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(log_file=log_file)
            
            assert log_file.exists()
            
            # Verify handler was added
            root_logger = logging.getLogger()
            file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
    
    def test_setup_logging_json_format(self):
        """Test logging setup with JSON format."""
        import logger
        logger._CONFIGURED = False
        
        setup_logging(json_format=True)
        
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            assert isinstance(handler.formatter, JSONFormatter)
    
    def test_setup_logging_no_console(self):
        """Test logging setup without console handler."""
        import logger
        logger._CONFIGURED = False
        
        setup_logging(console=False)
        
        root_logger = logging.getLogger()
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) == 0
    
    def test_setup_logging_idempotent(self):
        """Test that setup_logging can be called multiple times safely."""
        import logger
        logger._CONFIGURED = False
        
        setup_logging(log_level="DEBUG")
        initial_count = len(logging.getLogger().handlers)
        
        setup_logging(log_level="ERROR")
        # Should not add more handlers
        assert len(logging.getLogger().handlers) == initial_count

class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_creates_new(self):
        """Test that get_logger creates a new logger if not exists."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging()
        
        test_logger = get_logger("test_module")
        
        assert test_logger.name == "test_module"
        assert "test_module" in logger._LOGGERS
    
    def test_get_logger_returns_cached(self):
        """Test that get_logger returns cached logger."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging()
        
        logger1 = get_logger("cached_module")
        logger2 = get_logger("cached_module")
        
        assert logger1 is logger2
    
    def test_get_logger_auto_config(self):
        """Test that get_logger auto-configures if not set up."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        # Should not raise, should auto-configure
        test_logger = get_logger("auto_module")
        
        assert test_logger is not None
        assert logger._CONFIGURED is True

class TestJSONFormatter:
    """Tests for JSONFormatter class."""
    
    def test_format_basic(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
    
    def test_format_with_exception(self):
        """Test JSON formatting with exception info."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            output = formatter.format(record)
            parsed = json.loads(output)
            
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]
    
    def test_format_with_extra_fields(self):
        """Test JSON formatting with extra context fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"user_id": 123, "action": "login"}
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["user_id"] == 123
        assert parsed["action"] == "login"

class TestLogWithContext:
    """Tests for log_with_context function."""
    
    def test_log_with_context_basic(self):
        """Test basic logging with context."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging(console=True)
        
        test_logger = get_logger("context_test")
        
        # Capture log output
        with patch.object(test_logger, 'handle') as mock_handle:
            log_with_context(
                test_logger, 
                "INFO", 
                "Test message",
                user_id=123,
                action="test"
            )
            
            assert mock_handle.called
            call_args = mock_handle.call_args[0][0]
            assert call_args.msg == "Test message"
            assert call_args.extra_fields["user_id"] == 123
            assert call_args.extra_fields["action"] == "test"
    
    def test_log_with_context_invalid_level(self):
        """Test that invalid level raises ValueError."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging()
        
        test_logger = get_logger("invalid_level_test")
        
        with pytest.raises(ValueError):
            log_with_context(test_logger, "INVALID_LEVEL", "Message")

class TestLoggerIntegration:
    """Integration tests for logging functionality."""
    
    def test_logger_propagation(self):
        """Test that log messages propagate correctly."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "integration.log"
            setup_logging(log_level="DEBUG", log_file=log_file, console=False)
            
            test_logger = get_logger("integration_test")
            test_logger.debug("Debug message")
            test_logger.info("Info message")
            test_logger.warning("Warning message")
            test_logger.error("Error message")
            
            # Verify log file contains messages
            assert log_file.exists()
            content = log_file.read_text()
            
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
    
    def test_multiple_loggers_same_config(self):
        """Test that multiple loggers share the same configuration."""
        import logger
        logger._CONFIGURED = False
        logger._LOGGERS.clear()
        
        setup_logging(log_level="WARNING")
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.level == logging.WARNING
        assert logger2.level == logging.WARNING
        assert logger1.handlers == logger2.handlers
