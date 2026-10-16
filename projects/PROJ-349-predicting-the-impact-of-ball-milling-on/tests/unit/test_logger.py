"""
Unit tests for the logging infrastructure (src.utils.logger).
Verifies that ``get_logger`` returns a logger that writes to stdout
and that the configurable log level works as expected.
"""
import sys

import pytest

from src.utils.logger import get_logger, set_log_level, reset_logger

@pytest.fixture(autouse=True)
def clean_logger():
    """
    Ensure that each test starts with a fresh logger configuration.
    """
    reset_logger()
    yield
    reset_logger()

def test_logger_writes_to_stdout(capsys):
    logger = get_logger("test_logger")
    logger.info("Hello stdout")
    captured = capsys.readouterr()
    # The message should be captured on stdout (not stderr)
    assert "Hello stdout" in captured.out
    assert captured.err == ""

def test_logger_respects_set_log_level(capsys):
    # Set to DEBUG and emit a debug message
    set_log_level("DEBUG")
    logger = get_logger("debug_logger")
    logger.debug("debug message")
    captured = capsys.readouterr()
    assert "debug message" in captured.out

    # Reset to INFO and ensure DEBUG messages are suppressed
    set_log_level("INFO")
    logger.debug("should not appear")
    captured = capsys.readouterr()
    assert captured.out == ""  # No output for suppressed debug level