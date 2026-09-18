"""
Unit test for the logger utility.

The test writes a log entry using ``log_info`` and then verifies that the
entry appears in the expected log file.
"""

import os
from pathlib import Path

import pytest

# Import the logger helpers
from utils.logger import (
    get_pipeline_logger,
    log_info,
    log_debug,
    log_warning,
    log_error,
    log_critical,
    log_exception_details,
)


@pytest.fixture(scope="function")
def clean_log_file(tmp_path_factory):
    """
    Provide a fresh log file for each test case.
    The logger reads its destination from ``config.yaml``; however, the
    logger also falls back to the default ``data/logs/pipeline.log`` when
    that key is missing. We therefore ensure that the default location is
    cleared before each test.
    """
    # Ensure the default log directory exists
    default_log_path = Path("data/logs/pipeline.log")
    if default_log_path.is_file():
        default_log_path.unlink()
    yield default_log_path
    # Cleanup after test
    if default_log_path.is_file():
        default_log_path.unlink()


def test_logger_writes_and_reads_entry(clean_log_file: Path):
    """
    Write a test message and assert it is present in the log file.
    """
    test_message = "UNIT TEST LOG ENTRY"
    # Use the high‑level helper – this will trigger lazy logger creation.
    log_info(test_message)

    # Verify the file exists
    assert clean_log_file.is_file(), "Log file was not created"

    # Read the file contents
    with clean_log_file.open("r", encoding="utf-8") as f:
        contents = f.read()

    # The log entry should contain the test message
    assert test_message in contents, "Log entry not found in log file"


def test_logger_multiple_levels(clean_log_file: Path):
    """
    Emit log entries at all supported levels and ensure they are recorded.
    """
    messages = {
        "debug": "debug message",
        "info": "info message",
        "warning": "warning message",
        "error": "error message",
        "critical": "critical message",
    }

    log_debug(messages["debug"])
    log_info(messages["info"])
    log_warning(messages["warning"])
    log_error(messages["error"])
    log_critical(messages["critical"])

    # Read back the file
    with clean_log_file.open("r", encoding="utf-8") as f:
        log_text = f.read()

    for level, msg in messages.items():
        assert msg in log_text, f"{level.upper()} message not found in log"


def test_log_exception_details(clean_log_file: Path):
    """
    Verify that an exception's traceback is logged.
    """
    try:
        raise ValueError("sample error")
    except ValueError as exc:
        log_exception_details(exc, "Caught exception in test")

    with clean_log_file.open("r", encoding="utf-8") as f:
        log_text = f.read()

    assert "Caught exception in test" in log_text
    assert "ValueError: sample error" in log_text
    # The traceback contains the line "raise ValueError" – ensure at least
    # part of it appears.
    assert "raise ValueError" in log_text