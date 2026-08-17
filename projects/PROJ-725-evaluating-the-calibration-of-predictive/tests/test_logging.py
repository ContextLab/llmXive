"""
Tests for code/utils/logging.py
"""

import logging
import json
import os
import tempfile
from io import StringIO

from code.utils.logging import setup_logging, get_logger, log_with_context, ConsoleFormatter


def test_setup_logging_console():
    """Test that setup_logging configures a console handler."""
    logger = get_logger("test_console")
    setup_logging(log_level="INFO", json_format=False)

    # Verify logger level
    assert logger.level == logging.INFO or logger.level == logging.NOTSET

    # Verify handler exists
    assert len(logging.getLogger().handlers) > 0


def test_setup_logging_json():
    """Test that setup_logging configures JSON formatting."""
    setup_logging(log_level="DEBUG", json_format=True)
    logger = get_logger("test_json")

    # Capture log output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.getLogger().handlers[0].formatter)
    logger.addHandler(handler)

    logger.info("Test message")
    output = stream.getvalue()

    # Verify JSON structure
    log_entry = json.loads(output.strip())
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test message"
    assert "timestamp" in log_entry


def test_setup_logging_file():
    """Test that setup_logging writes to a file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
        tmp_path = tmp.name

    try:
        setup_logging(log_level="INFO", log_file=tmp_path)
        logger = get_logger("test_file")
        logger.info("File log test")

        # Force flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        with open(tmp_path, "r") as f:
            content = f.read()

        assert "File log test" in content
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_log_with_context():
    """Test that log_with_context includes extra fields."""
    setup_logging(log_level="INFO", json_format=True)
    logger = get_logger("test_context")

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.getLogger().handlers[0].formatter)
    logger.addHandler(handler)

    log_with_context(logger, logging.INFO, "Context test", user_id=123, action="run")
    output = stream.getvalue()

    log_entry = json.loads(output.strip())
    assert log_entry["user_id"] == 123
    assert log_entry["action"] == "run"
