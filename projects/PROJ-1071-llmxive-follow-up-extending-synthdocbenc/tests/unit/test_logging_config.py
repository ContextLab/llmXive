import os
import json
import tempfile
import logging
from datetime import datetime

import pytest

# Import the module under test
from code.logging_config import JsonFormatter, setup_logging, get_logger

def test_json_formatter_structure():
    """Test that the JsonFormatter produces valid JSON with required fields."""
    formatter = JsonFormatter()
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # Create a log record manually
    record = logger.makeRecord(
        name="test_logger",
        level=logging.INFO,
        fn="test_file.py",
        lno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    
    assert "timestamp" in parsed
    assert "level" in parsed
    assert parsed["level"] == "INFO"
    assert "logger" in parsed
    assert parsed["logger"] == "test_logger"
    assert "message" in parsed
    assert parsed["message"] == "Test message"
    assert "module" in parsed
    assert parsed["module"] == "test_file"
    assert "function" in parsed
    assert "line" in parsed
    assert parsed["line"] == 10

def test_setup_logging_to_file():
    """Test that setup_logging creates a file and writes structured JSON logs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = os.path.join(tmp_dir, "test.log")
        
        # Setup logging to the file
        setup_logging(log_file=log_file, log_level=logging.INFO)
        
        # Get a logger and log something
        logger = get_logger("test_file_logger")
        logger.info("Log to file")
        
        # Verify file exists
        assert os.path.exists(log_file)
        
        # Verify content is valid JSON
        with open(log_file, "r") as f:
            line = f.readline()
            parsed = json.loads(line)
            assert parsed["message"] == "Log to file"
            assert parsed["level"] == "INFO"

def test_setup_logging_to_console():
    """Test that setup_logging adds a console handler."""
    # This test mainly ensures no exception is raised during setup
    # and that the root logger has handlers.
    setup_logging(log_file=None, log_level=logging.WARNING)
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0

def test_get_logger_returns_configured_instance():
    """Test that get_logger returns an instance of logging.Logger."""
    logger = get_logger("custom_name")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "custom_name"
