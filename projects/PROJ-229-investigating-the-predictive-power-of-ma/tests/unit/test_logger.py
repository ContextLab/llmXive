import pytest
import logging
import os
from pathlib import Path
from code.utils.logger import setup_logger, get_pipeline_logger


def test_setup_logger_creates_handlers():
    """Test that setup_logger creates console and file handlers."""
    logger = setup_logger("test_setup_logger")
    
    assert len(logger.handlers) >= 2  # Console + File
    
    has_console = False
    has_file = False
    
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            has_console = True
        if isinstance(handler, logging.FileHandler):
            has_file = True
    
    assert has_console, "Console handler missing"
    assert has_file, "File handler missing"


def test_get_pipeline_logger_returns_singleton():
    """Test that get_pipeline_logger returns the same instance."""
    logger1 = get_pipeline_logger()
    logger2 = get_pipeline_logger()
    assert logger1 is logger2


def test_logger_output_format(capsys):
    """Test that logger output contains expected format."""
    logger = setup_logger("test_format_logger")
    logger.info("Test message")
    
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    assert "INFO" in captured.out


def test_log_file_creation(tmp_path):
    """Test that log file is created in the specified directory."""
    # We can't easily override the config path in this simple test without mocking,
    # but we can verify the file handler exists and the path is valid.
    # For a robust test, we'd mock get_config to point to tmp_path.
    
    # Instead, we verify that the handler path is a Path object or string
    logger = setup_logger("test_file_logger")
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            log_path = Path(handler.baseFilename)
            assert log_path.exists(), f"Log file {log_path} was not created"
            assert log_path.suffix == ".log", "Log file must have .log extension"