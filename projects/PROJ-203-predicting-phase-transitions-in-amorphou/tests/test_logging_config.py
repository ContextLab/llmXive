"""
Test for the simple pipeline logger created by ``utils.logging_config.setup_logger``.
The test verifies that:
  1. The function returns a ``logging.Logger`` instance.
  2. After emitting an INFO‑level message, the message appears in
     ``data/logs/pipeline.log``.
"""

import os
import logging

from llmxive_toolkit import paths
from utils.logging_config import setup_logger


def test_setup_logger_writes_to_file(tmp_path, monkeypatch):
    """
    Ensure that the logger writes a test entry to the expected file.
    """
    # Monkey‑patch the paths.data function to point to a temporary directory
    # so the test does not interfere with any real log files.
    def fake_data(*parts):
        return tmp_path.joinpath(*parts)

    monkeypatch.setattr("llmxive_toolkit.paths.data", fake_data)

    logger = setup_logger()
    assert isinstance(logger, logging.Logger)

    test_message = "TEST LOG ENTRY"
    logger.info(test_message)

    # Resolve the path that the logger should have written to
    log_file = fake_data("logs", "pipeline.log")
    assert log_file.exists(), f"Log file {log_file} was not created"

    # Verify the content includes our test message
    content = log_file.read_text()
    assert test_message in content, "Log entry not found in pipeline.log"