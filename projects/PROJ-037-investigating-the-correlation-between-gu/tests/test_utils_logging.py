"""
Unit tests for logging utilities.
"""
import pytest
import logging
import tempfile
import os
from pathlib import Path

from code.utils.logging_utils import setup_logging, get_logger

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for logs."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup handled by caller or pytest fixture finalizer

def test_setup_logging_console_only():
    """Test logging setup with only console handler."""
    # Reset root logger handlers
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    root_logger.handlers.clear()

    try:
        setup_logging(log_level=logging.DEBUG)

        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)

def test_setup_logging_with_file(temp_logs_dir):
    """Test logging setup with file handler."""
    log_file = "test.log"
    setup_logging(log_level=logging.INFO, log_file=log_file, project_root=temp_logs_dir)

    log_path = temp_logs_dir / log_file
    assert log_path.exists()

def test_get_logger():
    """Test retrieving a named logger."""
    logger = get_logger("test.module")
    assert logger.name == "test.module"
    assert isinstance(logger, logging.Logger)

def test_get_logger_root():
    """Test retrieving the root logger."""
    logger = get_logger()
    assert logger.name == "root"
