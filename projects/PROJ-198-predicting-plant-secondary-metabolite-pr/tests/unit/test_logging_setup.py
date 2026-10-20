"""
Verify that the logging utility creates a log file when called with the default
configuration (no explicit log_file argument). The file should be located at
``logs/run.log`` relative to the project root.
"""

import logging
from pathlib import Path

import pytest

from code.utils.logging import setup_logging, get_logger

def test_logging_creates_file(tmp_path, monkeypatch):
    # Redirect the project root to a temporary directory for isolation
    monkeypatch.setattr("code.utils.logging.PROJECT_ROOT", tmp_path)
    log_file = tmp_path / "logs" / "run.log"

    # Ensure clean state
    if log_file.is_file():
        log_file.unlink()

    # Call setup_logging without specifying a log file
    setup_logging()
    logger = get_logger(__name__)
    logger.info("test message")

    assert log_file.is_file()
    contents = log_file.read_text()
    assert "test message" in contents
