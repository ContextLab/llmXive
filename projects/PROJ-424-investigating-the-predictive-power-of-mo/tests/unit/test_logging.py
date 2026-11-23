"""
Unit tests for logging utilities.
"""
import logging
import json
import tempfile
from pathlib import Path
import pytest

from utils.logging import (
    setup_logging,
    get_logger,
    log_event,
    JSONFormatter,
)


def test_setup_logging_console_only():
    """Test basic console logging setup."""
    logger = setup_logging(log_level="DEBUG")
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_setup_logging_with_file():
    """Test logging setup with file output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logging(log_level="INFO", log_file=log_file)
        
        assert len(logger.handlers) == 2
        assert log_file.exists()


def test_json_formatter():
    """Test JSON formatter produces valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    output = formatter.format(record)
    parsed = json.loads(output)
    
    assert "timestamp" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"


def test_get_logger():
    """Test getting a named logger."""
    logger = get_logger("test.module")
    assert logger.name == "test.module"


def test_log_event():
    """Test structured event logging."""
    logger = setup_logging(log_level="DEBUG")
    test_logger = get_logger("test.event")
    
    # This should not raise
    log_event(
        test_logger,
        event_type="test_event",
        message="Test event message",
        level="INFO",
        extra_key="extra_value",
        number=42
    )
