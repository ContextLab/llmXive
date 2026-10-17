"""
Tests for the global logging infrastructure defined in ``src.utils.logging``.
"""

import os
import re
from pathlib import Path

import pytest

# Import the utilities we just created.
from src.utils.logging import get_logger, exception_handler

@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    """
    Fixture that provides a temporary log file path and ensures the logger
    writes to it.
    """
    # Use a temporary file inside the pytest temporary directory.
    custom_log = tmp_path / "test_run.log"
    # Force creation of a fresh logger that points at this file.
    logger = get_logger("test_logger", log_file=custom_log, level=10)  # DEBUG level
    # Ensure the logger has no leftover handlers from previous imports.
    for h in list(logger.handlers):
        logger.removeHandler(h)
    # Re‑add handlers with the custom path.
    logger.handlers.clear()
    # Re‑configure via the helper (captures the custom path).
    _ = get_logger("test_logger", log_file=custom_log, level=10)
    return custom_log


def test_logger_writes_to_file(log_path: Path):
    """The logger should create the file and contain the logged message."""
    logger = get_logger("test_logger_file", log_file=log_path, level=10)
    test_message = "Hello from test_logger_writes_to_file"
    logger.info(test_message)

    # Flush handlers to ensure the message is written.
    for handler in logger.handlers:
        handler.flush()

    assert log_path.is_file(), "Log file was not created"
    content = log_path.read_text(encoding="utf-8")
    # Simple regex to find the message (timestamp and level are variable).
    pattern = re.escape(test_message)
    assert re.search(pattern, content), "Logged message not found in file"


def test_exception_handler_decorator(log_path: Path):
    """The decorator should log the exception and return ``None``."""
    logger = get_logger("exception_test", log_file=log_path, level=10)

    @exception_handler
    def faulty():
        raise ValueError("intentional error for testing")

    result = faulty()
    assert result is None, "Decorator should swallow the exception and return None"

    # Ensure the exception traceback was logged.
    for handler in logger.handlers:
        handler.flush()
    content = log_path.read_text(encoding="utf-8")
    assert "intentional error for testing" in content
    assert "Traceback (most recent call last)" in content