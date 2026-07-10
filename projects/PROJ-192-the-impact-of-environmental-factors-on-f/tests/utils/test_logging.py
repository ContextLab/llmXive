"""
Unit tests for src/utils/logging.py
"""

import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from src.utils.logging import JsonFormatter, get_logger, log_event


def test_json_formatter_output():
    """Test that the formatter produces valid JSON."""
    formatter = JsonFormatter()
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
    assert "logger" in parsed


def test_logger_initialization():
    """Test that get_logger returns a configured logger."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        logger = get_logger("test_logger", log_file=log_file, console=False)

        assert logger is not None
        assert len(logger.handlers) == 1

        logger.info("Test log")

        with open(log_file, "r") as f:
            line = f.readline()
            parsed = json.loads(line)
            assert parsed["message"] == "Test log"


def test_log_event_with_extra():
    """Test log_event function with extra keyword arguments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test_event.log")
        logger = get_logger("test_event_logger", log_file=log_file, console=False)

        log_event(
            logger,
            event_type="data_download",
            message="Download started",
            url="http://example.com",
            size_mb=10,
        )

        with open(log_file, "r") as f:
            line = f.readline()
            parsed = json.loads(line)
            assert parsed["event_type"] == "data_download"
            assert parsed["url"] == "http://example.com"
            assert parsed["size_mb"] == 10
