"""
Unit tests for the logging infrastructure.
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Assuming the project structure is code/utils/logging.py
# and tests are in code/tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import (
    get_logger,
    configure_root_logger,
    get_module_logger,
    DEFAULT_LOG_LEVEL,
    LOG_FORMAT,
)


def test_get_logger_default():
    """Test that get_logger returns a logger with default settings."""
    logger = get_logger("test_default")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_default"
    assert logger.level == DEFAULT_LOG_LEVEL
    # Should have at least one handler (console)
    assert len(logger.handlers) >= 1


def test_get_logger_custom_level():
    """Test that get_logger respects custom log level."""
    logger = get_logger("test_custom_level", level=logging.DEBUG)
    assert logger.level == logging.DEBUG


def test_get_logger_with_file(tmp_path):
    """Test that get_logger creates a file handler when log_file is provided."""
    log_file = tmp_path / "test.log"
    logger = get_logger("test_file", log_file=log_file)
    assert len(logger.handlers) >= 2  # Console + File

    # Verify the file was created
    assert log_file.exists()

    # Log a message
    logger.info("Test message")

    # Verify the file has content
    with open(log_file, "r") as f:
        content = f.read()
    assert "Test message" in content
    assert "test_file" in content


def test_get_logger_no_duplicate_handlers():
    """Test that calling get_logger multiple times doesn't add duplicate handlers."""
    logger = get_logger("test_no_dup")
    initial_count = len(logger.handlers)

    logger = get_logger("test_no_dup")
    assert len(logger.handlers) == initial_count


def test_get_module_logger():
    """Test get_module_logger creates a logger with the correct name."""
    logger = get_module_logger("my_module")
    assert logger.name == "my_module"


def test_configure_root_logger(tmp_path):
    """Test that configure_root_logger sets up the root logger."""
    log_file = tmp_path / "root.log"
    root_logger = configure_root_logger(log_file=log_file)

    assert isinstance(root_logger, logging.Logger)
    assert root_logger.level == DEFAULT_LOG_LEVEL
    assert len(root_logger.handlers) >= 2  # Console + File

    # Verify the file was created
    assert log_file.exists()

    # Log a message using the root logger
    root_logger.warning("Root warning")

    # Verify the file has content
    with open(log_file, "r") as f:
        content = f.read()
    assert "Root warning" in content
    assert "WARNING" in content


def test_log_format(tmp_path):
    """Test that log messages follow the expected format."""
    log_file = tmp_path / "format.log"
    logger = get_logger("test_format", log_file=log_file)

    logger.info("Format test message")

    with open(log_file, "r") as f:
        line = f.readline().strip()

    # Check for expected components in the log line
    assert "test_format" in line
    assert "INFO" in line
    assert "Format test message" in line
    # Check for timestamp (simplified check)
    assert len(line) > 20  # Should be longer than just the message
