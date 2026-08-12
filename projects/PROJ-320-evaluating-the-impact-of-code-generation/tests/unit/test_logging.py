"""
tests/unit/test_logging.py

Unit tests for code/utils/logging.py
"""
import pytest
import logging
import tempfile
import os
from pathlib import Path
from code.utils.logging import setup_logging, get_logger

def test_setup_logging_creates_directory():
    """Test that setup_logging creates the log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = os.path.join(tmpdir, "logs")
        setup_logging(log_dir=log_dir, level=logging.INFO)
        assert os.path.exists(log_dir)

def test_get_logger_returns_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"

def test_logger_levels():
    """Test that logger respects level settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = os.path.join(tmpdir, "logs")
        setup_logging(log_dir=log_dir, level=logging.WARNING)
        
        logger = get_logger("test_level")
        assert logger.level == logging.WARNING or logger.level == logging.NOTSET