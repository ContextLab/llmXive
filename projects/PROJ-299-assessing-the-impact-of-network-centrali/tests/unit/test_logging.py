"""
Unit tests for the logging infrastructure (T005).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import logging

# Import the module under test
from code.utils.logging_config import (
    setup_logging,
    get_logger,
    log_event,
    JSONFormatter,
)

class TestJSONFormatter:
    def test_format_basic_message(self):
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
        data = json.loads(output)
        
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["module"] == "test"

    def test_format_with_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except Exception:
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
            data = json.loads(output)
            
            assert data["level"] == "ERROR"
            assert "exception" in data
            assert "ValueError" in data["exception"]

    def test_format_with_extra_data(self):
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
        record.extra_data = {"user_id": 123, "action": "login"}
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["user_id"] == 123
        assert data["action"] == "login"

class TestSetupLogging:
    def test_creates_log_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)
            
            assert log_path.exists()
            
            # Log something and verify file grows
            logger.info("Test entry")
            assert log_path.stat().st_size > 0

    def test_returns_root_logger(self):
        logger = setup_logging(console_output=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "root"

class TestGetLogger:
    def test_returns_named_logger(self):
        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert isinstance(logger, logging.Logger)

class TestLogEvent:
    def test_logs_with_extra_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            setup_logging(log_file=log_path, console_output=False)
            logger = get_logger("test_event")
            
            log_event(logger, logging.INFO, "Event message", {"key": "value"})
            
            # Read and verify
            with open(log_path, 'r') as f:
                line = f.readline().strip()
                data = json.loads(line)
                
                assert data["message"] == "Event message"
                assert data["key"] == "value"
                assert data["level"] == "INFO"