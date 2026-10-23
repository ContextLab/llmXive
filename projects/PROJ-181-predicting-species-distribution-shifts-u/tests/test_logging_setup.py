"""
Unit tests for the logging setup implemented in ``code/logging_setup.py``.
"""
import os
from pathlib import Path

import pytest

from code.logging_setup import initialize_logging
from llmxive_toolkit import paths

def test_initialize_logging_creates_file(tmp_path, monkeypatch):
    # Redirect the project root to a temporary directory for isolation
    monkeypatch.chdir(tmp_path)

    # Ensure a minimal logging config exists
    config_path = tmp_path / "logs" / "logging_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "format: \"% (asctime)s - %(name)s - %(levelname)s - %(message)s\"\n"
        "level: INFO\n",
        encoding="utf-8",
    )

    # Initialise logging – it should create a log file named after the script
    log_file = paths.logs("test_script.log")
    initialize_logging(log_file)

    # Verify the log file exists and is writable
    assert log_file.is_file()
    # Write a test log entry and ensure it appears in the file
    import logging

    logger = logging.getLogger("test_logger")
    logger.info("test message")
    contents = log_file.read_text(encoding="utf-8")
    assert "test message" in contents