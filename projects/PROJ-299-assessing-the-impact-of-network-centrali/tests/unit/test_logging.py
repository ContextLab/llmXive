"""
Unit tests for the logging infrastructure (T005).
Verifies that logs are machine-readable JSON and contain required fields.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import setup_logging, get_logger, log_event, JSONFormatter

def test_json_formatter():
    """Test that JSONFormatter produces valid JSON strings."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    
    # Must be valid JSON
    parsed = json.loads(formatted)
    assert "timestamp" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert parsed["logger"] == "test_logger"

def test_log_event_with_extra_data():
    """Test that log_event includes extra data in the JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        
        setup_logging(log_file=log_file, log_level=logging.DEBUG, console_output=False)
        logger = get_logger("test_extra")
        
        # Log with extra data
        log_event(logger, logging.INFO, "Event with extra", user_id=123, action="login")
        
        # Read and verify
        with open(log_file, 'r') as f:
            line = f.readline()
            parsed = json.loads(line)
            
        assert parsed["user_id"] == 123
        assert parsed["action"] == "login"
        assert parsed["message"] == "Event with extra"

def test_setup_logging_creates_file():
    """Test that setup_logging creates the log file and directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "subdir" / "pipeline.log"
        
        setup_logging(log_file=log_file, log_level=logging.INFO, console_output=False)
        logger = get_logger("test_setup")
        logger.info("Setup test")
        
        assert log_file.exists()
        
        # Verify content is JSON
        with open(log_file, 'r') as f:
            line = f.readline()
            json.loads(line) # Should not raise

def test_log_event():
    """Test the log_event helper function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        setup_logging(log_file=log_file, log_level=logging.DEBUG, console_output=False)
        logger = get_logger("test_main")
        
        log_event(logger, logging.WARNING, "Warning message", code=42)
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Warning message" in content
            assert "42" in content
            # Verify it's valid JSON lines
            for line in content.strip().split('\n'):
                json.loads(line)

if __name__ == "__main__":
    test_json_formatter()
    test_log_event_with_extra_data()
    test_setup_logging_creates_file()
    test_log_event()
    print("All logging tests passed.")
