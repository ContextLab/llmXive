"""
Unit tests for the logging infrastructure.
"""
import logging
import sys
import json
import tempfile
from pathlib import Path
import pytest

from logger import (
    JSONFormatter,
    setup_logging,
    get_logger,
    log_with_context,
    get_logger_for_module
)


class TestJSONFormatter:
    """Tests for the JSONFormatter class."""
    
    def test_format_basic_log(self):
        """Test formatting a basic log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test"
        assert "timestamp" in log_data
    
    def test_format_with_exception(self):
        """Test formatting a log record with exception info."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]
    
    def test_format_with_context(self):
        """Test formatting a log record with custom context."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Context test",
            args=(),
            exc_info=None
        )
        record.context = {"user_id": 123, "action": "test"}
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "context" in log_data
        assert log_data["context"]["user_id"] == 123


class TestSetupLogging:
    """Tests for the setup_logging function."""
    
    def test_setup_console_only(self):
        """Test setup with only console output."""
        setup_logging(console_output=True, log_level=logging.DEBUG)
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)
    
    def test_setup_with_file(self):
        """Test setup with file output."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            setup_logging(log_file=log_file, console_output=False)
            
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 1
            assert isinstance(root_logger.handlers[0], logging.FileHandler)
            
            # Write a log and verify file exists
            logger = logging.getLogger()
            logger.info("Test message")
            assert log_file.exists()
    
    def test_setup_json_format(self):
        """Test setup with JSON formatting."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.json"
            setup_logging(log_file=log_file, use_json=True, console_output=False)
            
            logger = logging.getLogger()
            logger.info("JSON test")
            
            # Read and parse the log file
            with open(log_file, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
            
            assert "timestamp" in log_data
            assert "level" in log_data


class TestGetLogger:
    """Tests for the get_logger function."""
    
    def test_get_logger_with_name(self):
        """Test getting a logger with a specific name."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"
    
    def test_get_logger_without_name(self):
        """Test getting the root logger when no name is provided."""
        logger = get_logger()
        assert logger.name == ""  # Root logger has empty name


class TestLogWithContext:
    """Tests for the log_with_context function."""
    
    def test_log_with_context(self):
        """Test logging with additional context."""
        logger = get_logger("test_context")
        logger.handlers.clear()  # Remove existing handlers for clean test
        
        # Add a string handler to capture output
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        log_with_context(logger, logging.INFO, "Test message", {"key": "value"})
        
        output = stream.getvalue()
        log_data = json.loads(output.strip())
        
        assert log_data["message"] == "Test message"
        assert log_data["context"]["key"] == "value"


class TestGetLoggerForModule:
    """Tests for the get_logger_for_module function."""
    
    def test_get_logger_for_module(self):
        """Test getting a logger for a specific module."""
        logger = get_logger_for_module("my_module.submodule")
        assert logger.name == "my_module.submodule"
