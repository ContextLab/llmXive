import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.logging_config import setup_logging, get_logger, LOG_DIR, LOG_FILE


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for log files."""
    return str(tmp_path)


def test_setup_logging_creates_directory(temp_log_dir):
    """Test that setup_logging creates the log directory if it doesn't exist."""
    non_existent_dir = os.path.join(temp_log_dir, "new_logs")
    assert not os.path.exists(non_existent_dir)

    logger = setup_logging(log_dir=non_existent_dir, log_file="test.log", console=False)

    assert os.path.exists(non_existent_dir)
    assert isinstance(logger, logging.Logger)


def test_setup_logging_creates_file(temp_log_dir):
    """Test that setup_logging creates the log file."""
    log_path = os.path.join(temp_log_dir, "test_logs")
    log_file = "test.log"

    logger = setup_logging(log_dir=log_path, log_file=log_file, console=False)

    full_path = os.path.join(log_path, log_file)
    assert os.path.exists(full_path)


def test_setup_logging_adds_handlers(temp_log_dir):
    """Test that setup_logging adds the correct handlers."""
    logger = setup_logging(log_dir=temp_log_dir, log_file="test.log", console=False)

    # Should have at least one file handler
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0


def test_setup_logging_console_handler(temp_log_dir):
    """Test that console handler is added when console=True."""
    logger = setup_logging(log_dir=temp_log_dir, log_file="test.log", console=True)

    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    # Should have at least the console handler (stdout)
    assert len(stream_handlers) >= 1


def test_get_logger_returns_configured_logger(temp_log_dir):
    """Test that get_logger returns a logger that inherits the root configuration."""
    setup_logging(log_dir=temp_log_dir, log_file="test.log", console=False)

    child_logger = get_logger("test_module")

    assert isinstance(child_logger, logging.Logger)
    assert child_logger.name == "test_module"
    # The child logger should inherit the level and handlers from the root
    assert child_logger.level == logging.NOTSET  # Default, inherits from root
    assert len(child_logger.handlers) == 0  # No direct handlers, uses propagation
    assert child_logger.parent is not None


def test_logging_writes_message(temp_log_dir):
    """Test that logging actually writes to the file."""
    log_path = os.path.join(temp_log_dir, "write_test_logs")
    log_file = "write_test.log"

    setup_logging(log_dir=log_path, log_file=log_file, console=False, level=logging.INFO)
    logger = get_logger("test_write")

    test_msg = "Test log message for verification"
    logger.info(test_msg)

    # Force flush
    for handler in logging.getLogger().handlers:
        handler.flush()

    full_path = os.path.join(log_path, log_file)
    with open(full_path, "r") as f:
        content = f.read()

    assert test_msg in content
    assert "INFO" in content
    assert "test_write" in content