import pytest
import logging
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger import (
    StructuredFormatter, 
    ConsoleFormatter, 
    get_logger, 
    log_structured_event, 
    log_data_integrity_error,
    configure_root_logger
)
from exceptions import DataIntegrityError

class TestStructuredFormatter:
    def test_format_basic_log(self):
        formatter = StructuredFormatter()
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
        log_entry = json.loads(output)
        
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert "timestamp" in log_entry
        assert log_entry["logger"] == "test"

    def test_format_with_extra_data(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        record.extra_data = {"dataset_id": "ds001", "subject": "sub-01"}
        
        output = formatter.format(record)
        log_entry = json.loads(output)
        
        assert log_entry["context"]["dataset_id"] == "ds001"
        assert log_entry["context"]["subject"] == "sub-01"

    def test_format_with_exception(self):
        formatter = StructuredFormatter()
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
            log_entry = json.loads(output)
            
            assert log_entry["exception"]["type"] == "ValueError"
            assert log_entry["exception"]["message"] == "Test error"
            assert "traceback" in log_entry["exception"]

class TestConsoleFormatter:
    def test_format_basic_log(self):
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Console test",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        
        assert "INFO" in output
        assert "Console test" in output

class TestLoggingFunctions:
    def setup_method(self):
        # Ensure logger is configured for tests
        configure_root_logger()
    
    def test_log_structured_event(self):
        # This should not raise
        log_structured_event(
            event_type="TEST_EVENT",
            message="Testing structured logging",
            level="INFO"
        )
    
    def test_log_data_integrity_error(self):
        error = DataIntegrityError("Missing required field: sampling_frequency")
        log_data_integrity_error(error, context={"file": "dataset_description.json"})
    
    def test_get_logger(self):
        logger = get_logger("custom_test_logger")
        assert logger.name == "custom_test_logger"
        assert isinstance(logger, logging.Logger)
