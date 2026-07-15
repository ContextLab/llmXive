"""
Unit tests for src/utils/logging.py
"""

import logging
import json
import io
import sys
from unittest.mock import patch, MagicMock

import pytest

from src.utils.logging import (
    setup_logging,
    log_step_start,
    log_step_complete,
    log_step_error,
    log_validation_result,
    StructuredFormatter,
)


@pytest.fixture
def logger_with_stream():
    """Create a logger that writes to a StringIO buffer for inspection."""
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = setup_logging(name="test_logger", level=logging.INFO)
    # Clear existing handlers to avoid noise
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger, buffer


def test_setup_logging_returns_logger():
    """Test that setup_logging returns a configured logger."""
    logger = setup_logging(name="test_setup")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_setup"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_log_step_start(logger_with_stream):
    """Test logging the start of a step."""
    logger, buffer = logger_with_stream
    log_step_start(logger, "test_step", {"param": "value"})

    output = buffer.getvalue()
    assert "Starting step: test_step" in output
    assert "test_step" in output


def test_log_step_complete(logger_with_stream):
    """Test logging the completion of a step."""
    logger, buffer = logger_with_stream
    log_step_complete(logger, "test_step", duration_seconds=1.5)

    output = buffer.getvalue()
    assert "Completed step: test_step" in output
    assert "1.5" in output


def test_log_step_error(logger_with_stream):
    """Test logging an error in a step."""
    logger, buffer = logger_with_stream
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_step_error(logger, "test_step", e)

    output = buffer.getvalue()
    assert "Error in step: test_step" in output
    assert "Test error" in output
    assert "ValueError" in output


def test_log_validation_result_passed(logger_with_stream):
    """Test logging a passed validation."""
    logger, buffer = logger_with_stream
    log_validation_result(logger, "check_data_integrity", passed=True)

    output = buffer.getvalue()
    assert "Validation Check: check_data_integrity - PASSED" in output


def test_log_validation_result_failed(logger_with_stream):
    """Test logging a failed validation."""
    logger, buffer = logger_with_stream
    log_validation_result(logger, "check_data_integrity", passed=False)

    output = buffer.getvalue()
    assert "Validation Check: check_data_integrity - FAILED" in output


def test_structured_formatter_json_output():
    """Test that StructuredFormatter produces valid JSON."""
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.created = 1234567890.0

    output = formatter.format(record)
    parsed = json.loads(output)

    assert "timestamp" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert parsed["logger"] == "test"


def test_structured_formatter_with_exception():
    """Test that StructuredFormatter includes exception info."""
    formatter = StructuredFormatter()
    try:
        raise RuntimeError("Boom")
    except Exception:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="Something broke",
        args=(),
        exc_info=exc_info
    )
    record.created = 1234567890.0

    output = formatter.format(record)
    parsed = json.loads(output)

    assert "exception" in parsed
    assert "RuntimeError" in parsed["exception"]
    assert "Boom" in parsed["exception"]