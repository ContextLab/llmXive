"""
Unit tests for the logging utilities in ``code/utils/logging.py``.
The tests ensure that a logger can be obtained, that it has at least one
handler, and that ``setup_logging`` correctly writes log records to a file.
"""
import logging
import os
from pathlib import Path

from utils.logging import get_logger, setup_logging


def test_get_logger_returns_logger_with_handler():
    """``get_logger`` should return a logger that has at least one handler."""
    logger_name = "test_logger"
    logger = get_logger(logger_name)

    # The logger should be an instance of ``logging.Logger``
    assert isinstance(logger, logging.Logger)

    # It should have at least one handler attached (the console handler)
    assert len(logger.handlers) >= 1, "Logger has no handlers attached"


def test_setup_logging_writes_to_file(tmp_path: Path):
    """``setup_logging`` should create a log file and write messages to it."""
    log_file = tmp_path / "test.log"

    # Initialise file logging
    setup_logging(log_file)

    # Retrieve a logger and emit a message
    logger = get_logger("file_logger")
    test_message = "Logging test message"
    logger.info(test_message)

    # Ensure the log file now exists
    assert log_file.is_file(), "Log file was not created by setup_logging"

    # Read the contents of the log file and verify the message appears
    with open(log_file, "r", encoding="utf-8") as f:
        log_contents = f.read()

    assert test_message in log_contents, "Logged message not found in log file"