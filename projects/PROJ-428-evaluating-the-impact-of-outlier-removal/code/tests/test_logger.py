"""
Tests for the logging infrastructure.
"""

import logging
import os
from pathlib import Path
import tempfile
import shutil

from src.logger import get_logger, configure_logger


def test_get_logger_returns_instance():
    """Test that get_logger returns a valid Logger instance."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "llmXive"


def test_logger_has_handlers():
    """Test that the logger has both file and console handlers."""
    logger = get_logger()
    assert len(logger.handlers) >= 2  # At least file and console

    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "StreamHandler" in handler_types
    assert "FileHandler" in handler_types


def test_logger_writes_to_file():
    """Test that the logger actually writes to the state/pipeline.log file."""
    logger = get_logger("test_logger_file")
    test_message = "Test log message for file verification"
    logger.info(test_message)

    # Force flush to ensure file is written
    for handler in logger.handlers:
        handler.flush()

    state_dir = Path("state")
    log_file = state_dir / "pipeline.log"

    assert log_file.exists(), "Log file should exist in state directory"

    content = log_file.read_text()
    assert test_message in content, f"Test message '{test_message}' not found in log file"


def test_configure_logger_updates_level():
    """Test that configure_logger updates the logging level."""
    logger = configure_logger(level=logging.DEBUG, name="test_config_logger")
    assert logger.level == logging.DEBUG

    # Reset for next tests
    configure_logger(level=logging.INFO, name="test_config_logger")