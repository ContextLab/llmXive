"""
Unit tests for the project‑wide logger.

The test verifies that:
1. The logger creates ``logs/pipeline.log`` if it does not exist.
2. INFO and WARNING messages are correctly written to the file.
3. Re‑using ``get_logger`` does not duplicate log entries.
"""

import os
from pathlib import Path

import pytest

from code.utils.logger import get_logger, log_warning, LOG_FILE


@pytest.fixture(autouse=True)
def clean_log_file():
    """Remove the log file before each test run."""
    if LOG_FILE.is_file():
        LOG_FILE.unlink()
    # Ensure the directory is removed as well (if empty)
    if LOG_FILE.parent.is_dir():
        try:
            LOG_FILE.parent.rmdir()
        except OSError:
            # Directory not empty – ignore
            pass
    yield
    # Cleanup after test
    if LOG_FILE.is_file():
        LOG_FILE.unlink()
    if LOG_FILE.parent.is_dir():
        try:
            LOG_FILE.parent.rmdir()
        except OSError:
            pass


def test_logger_writes_info_and_warning():
    logger = get_logger("test_logger")
    logger.info("Test info message")
    log_warning("Test warning message")

    # The log file should now exist
    assert LOG_FILE.is_file(), "Log file was not created"

    content = LOG_FILE.read_text(encoding="utf-8")
    assert "Test info message" in content, "INFO message not found in log"
    assert "Test warning message" in content, "WARNING message not found in log"


def test_logger_is_singleton():
    """
    Ensure that calling ``get_logger`` multiple times does not add
    additional handlers, which would duplicate log entries.
    """
    logger1 = get_logger("singleton_test")
    logger1.info("First entry")
    logger2 = get_logger("singleton_test")
    logger2.info("Second entry")

    content = LOG_FILE.read_text(encoding="utf-8")
    # There should be exactly two log lines (one per call)
    lines = [line for line in content.splitlines() if "singleton_test" in line]
    assert len(lines) == 2, f"Expected 2 log lines, found {len(lines)}"