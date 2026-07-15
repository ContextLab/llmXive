"""
Unit tests for the logging infrastructure.
"""
import os
import tempfile
import logging
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.logger import setup_logging, get_logger, _logger_instance


@pytest.fixture
def clean_logger():
    """Resets the logger instance for each test."""
    # Reset global state
    import utils.logger
    utils.logger._logger_instance = None
    # Also clear root handlers to avoid interference
    logging.getLogger().handlers.clear()
    yield
    # Cleanup
    utils.logger._logger_instance = None
    logging.getLogger().handlers.clear()


def test_setup_logging_creates_file(clean_logger, tmp_path):
    """Test that setup_logging creates a log file."""
    log_dir = str(tmp_path / "logs")
    logger = setup_logging(log_dir=log_dir, enable_console=False, enable_file=True)
    
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    
    # Check that a file was created
    files = list(Path(log_dir).glob("run_*.log"))
    assert len(files) == 1, f"Expected 1 log file, found {len(files)}"


def test_get_logger_returns_instance(clean_logger):
    """Test that get_logger returns the configured instance."""
    setup_logging(enable_console=False, enable_file=False)
    logger = get_logger()
    
    assert logger is not None
    assert logger.name == "llmXive"


def test_sub_logger_name(clean_logger):
    """Test that get_logger creates sub-loggers correctly."""
    setup_logging(enable_console=False, enable_file=False)
    sub_logger = get_logger("models.baseline")
    
    assert sub_logger is not None
    assert sub_logger.name == "llmXive.models.baseline"


def test_logger_level(clean_logger):
    """Test that logger level is set correctly."""
    logger = setup_logging(level=logging.DEBUG, enable_console=False, enable_file=False)
    assert logger.level == logging.DEBUG
    
    logger2 = setup_logging(level=logging.WARNING, enable_console=False, enable_file=False)
    # Should return the same instance if already set, but for test isolation we assume fresh
    # If the singleton pattern returns the old one, we check the current state
    # In a real test with fixtures, we reset the singleton.
    # Here, we rely on the fixture resetting _logger_instance.
    assert logger2.level == logging.WARNING

from pathlib import Path
