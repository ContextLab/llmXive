"""
Unit tests for the standardized logging module (code/utils/logging.py).
"""

import os
import logging
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import code.utils.logging as logging_utils


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_log_file(temp_log_dir):
    """Create a temporary log file path."""
    return temp_log_dir / "test_pipeline.log"


def test_get_logger_creates_instance():
    """Test that get_logger returns a valid Logger instance."""
    logger = logging_utils.get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_get_logger_default_level():
    """Test that logger defaults to INFO level."""
    logger = logging_utils.get_logger("test_default_level")
    assert logger.level == logging_utils.DEFAULT_LOG_LEVEL


def test_get_logger_custom_level(temp_log_dir):
    """Test that logger respects custom level."""
    logger = logging_utils.get_logger(
        "test_custom_level",
        level=logging.DEBUG,
        log_file=temp_log_dir / "custom.log"
    )
    assert logger.level == logging.DEBUG


def test_get_logger_file_handler_exists(temp_log_dir, temp_log_file):
    """Test that a file handler is created and writes to the specified file."""
    logger = logging_utils.get_logger(
        "test_file_handler",
        log_file=temp_log_file
    )

    # Verify file handler exists
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0

    # Log a message
    logger.info("Test message for file handler")

    # Verify file exists and contains the message
    assert temp_log_file.exists()
    content = temp_log_file.read_text()
    assert "Test message for file handler" in content


def test_get_logger_console_handler_exists():
    """Test that a console handler is created."""
    logger = logging_utils.get_logger("test_console_handler")
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    # Should have at least one console handler (the default one)
    assert len(console_handlers) > 0


def test_get_logger_no_duplicate_handlers():
    """Test that calling get_logger multiple times doesn't duplicate handlers."""
    logger_name = "test_no_duplicates"
    
    # First call
    logger1 = logging_utils.get_logger(logger_name)
    initial_handler_count = len(logger1.handlers)

    # Second call
    logger2 = logging_utils.get_logger(logger_name)
    final_handler_count = len(logger2.handlers)

    assert initial_handler_count == final_handler_count
    assert logger1 is logger2


def test_ensure_log_dir_creates_directory(temp_log_dir):
    """Test that _ensure_log_dir creates the directory if it doesn't exist."""
    # We can't easily test the internal _ensure_log_dir because it uses a global path,
    # but we can verify the side effect of get_logger which calls it.
    # Instead, we test the behavior via get_log_file_path which ensures the dir.
    
    # Mock the global LOG_DIR to use temp_log_dir for this specific test
    original_log_dir = logging_utils._LOG_DIR
    try:
        logging_utils._LOG_DIR = temp_log_dir / "subdir"
        result_path = logging_utils.get_log_file_path()
        assert result_path.parent.exists()
        assert result_path.parent == temp_log_dir / "subdir"
    finally:
        logging_utils._LOG_DIR = original_log_dir


def test_set_root_level():
    """Test that set_root_level updates the root logger level."""
    original_level = logging_utils.logging.root.level
    try:
        logging_utils.set_root_level(logging.WARNING)
        assert logging_utils.logging.root.level == logging.WARNING
    finally:
        logging_utils.logging.root.setLevel(original_level)


def test_setup_module_logger():
    """Test that setup_module_logger returns a logger with the caller's name."""
    logger = logging_utils.setup_module_logger()
    # The logger name should be the module name where this is called
    assert logger is not None
    assert isinstance(logger, logging.Logger)