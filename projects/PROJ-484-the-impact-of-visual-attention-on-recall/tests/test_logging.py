"""
Tests for logging infrastructure.
"""
import json
import os
import logging
from pathlib import Path
from unittest.mock import patch

# Import the module to trigger setup
import code.logging_config as logging_config


def test_log_file_exists():
    """Test that the log file is created after setup."""
    log_path = Path(logging_config.LOG_FILE)
    # The setup_logging function creates the directory and file when the first log is written.
    # We force a log write to ensure the file exists.
    logger = logging.getLogger()
    logger.debug("Test log message for file creation")
    assert log_path.exists(), f"Log file {log_path} was not created."


def test_log_format_is_json():
    """Test that log entries are valid JSON."""
    logger = logging.getLogger()
    test_msg = "Testing JSON format"
    logger.debug(test_msg)

    log_path = Path(logging_config.LOG_FILE)
    # Read the last line
    with open(log_path, "r") as f:
        lines = f.readlines()
        last_line = lines[-1]

    try:
        parsed = json.loads(last_line)
    except json.JSONDecodeError:
        assert False, f"Log entry is not valid JSON: {last_line}"

    assert "message" in parsed
    assert parsed["message"] == test_msg
    assert "timestamp" in parsed
    assert "level" in parsed
    assert parsed["level"] == "DEBUG"


def test_rotating_handler_exists():
    """Test that a RotatingFileHandler is attached."""
    logger = logging.getLogger()
    handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
    assert len(handlers) > 0, "No RotatingFileHandler found in logger."