"""
Unit tests for the logging utility module.
"""

import pytest
import logging
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import importlib

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import (
    setup_logging,
    get_logger,
    log_step_start,
    log_step_success,
    log_step_failure,
    StructuredFormatter,
    LOG_DIR,
    LOG_FILE_NAME
)


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def reset_logging():
    """Reset the global logging state before each test."""
    # We need to reload the module to reset the global state
    import src.utils.logging as logging_module
    logging_module._configured = False
    logging_module._logger = None
    yield
    # Cleanup after test
    logging_module._configured = False
    logging_module._logger = None


def test_setup_logging_creates_logger(temp_log_dir, reset_logging):
    """Test that setup_logging creates and returns a logger."""
    logger = setup_logging(log_level=logging.INFO, log_dir=temp_log_dir)
    assert logger is not None
    assert logger.name == "gw_compression_pipeline"
    assert logger.level == logging.INFO


def test_setup_logging_creates_log_file(temp_log_dir, reset_logging):
    """Test that setup_logging creates the log file."""
    logger = setup_logging(log_level=logging.INFO, log_dir=temp_log_dir)
    log_file = temp_log_dir / LOG_FILE_NAME
    assert log_file.exists()


def test_setup_logging_console_handler(temp_log_dir, reset_logging):
    """Test that setup_logging adds a console handler."""
    logger = setup_logging(log_level=logging.INFO, log_dir=temp_log_dir)
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) > 0


def test_setup_logging_file_handler(temp_log_dir, reset_logging):
    """Test that setup_logging adds a file handler."""
    logger = setup_logging(log_level=logging.INFO, log_dir=temp_log_dir)
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0


def test_get_logger_returns_child(temp_log_dir, reset_logging):
    """Test that get_logger returns a child logger."""
    setup_logging(log_dir=temp_log_dir)
    child_logger = get_logger("data.download")
    assert child_logger.name == "gw_compression_pipeline.data.download"


def test_structured_formatter_outputs_json(temp_log_dir, reset_logging):
    """Test that StructuredFormatter produces valid JSON."""
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
    parsed = json.loads(output)
    assert "timestamp" in parsed
    assert "level" in parsed
    assert parsed["message"] == "Test message"


def test_log_step_start_logs_info(temp_log_dir, reset_logging, caplog):
    """Test that log_step_start logs an INFO message."""
    setup_logging(log_dir=temp_log_dir, log_level=logging.INFO)
    with caplog.at_level(logging.INFO, logger="gw_compression_pipeline.test_step"):
        log_step_start("test_step", param1="value1")
    
    # Check that the log message exists
    assert any("Step 'test_step' started" in record.message for record in caplog.records)


def test_log_step_success_logs_info(temp_log_dir, reset_logging, caplog):
    """Test that log_step_success logs an INFO message."""
    setup_logging(log_dir=temp_log_dir, log_level=logging.INFO)
    with caplog.at_level(logging.INFO, logger="gw_compression_pipeline.test_step"):
        log_step_success("test_step", duration=1.5)
    
    assert any("Step 'test_step' completed successfully" in record.message for record in caplog.records)


def test_log_step_failure_logs_error(temp_log_dir, reset_logging, caplog):
    """Test that log_step_failure logs an ERROR message."""
    setup_logging(log_dir=temp_log_dir, log_level=logging.ERROR)
    test_error = ValueError("Test error")
    
    with caplog.at_level(logging.ERROR, logger="gw_compression_pipeline.test_step"):
        log_step_failure("test_step", error=test_error)
    
    assert any("Step 'test_step' failed" in record.message for record in caplog.records)
    assert any("Test error" in record.message for record in caplog.records)


def test_logging_idempotent(temp_log_dir, reset_logging):
    """Test that calling setup_logging multiple times doesn't duplicate handlers."""
    logger1 = setup_logging(log_dir=temp_log_dir)
    initial_handler_count = len(logger1.handlers)
    
    logger2 = setup_logging(log_dir=temp_log_dir)
    assert logger1 is logger2
    assert len(logger2.handlers) == initial_handler_count