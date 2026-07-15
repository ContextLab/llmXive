"""Tests for logging utilities."""
import logging
import tempfile
from pathlib import Path

from src.utils.logging import get_logger


def test_logger_creation():
    logger = get_logger("test_logger")
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO


def test_logger_file_handler():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        logger = get_logger("test_file_logger", log_dir=log_dir)
        
        logger.info("Test message")
        
        log_file = log_dir / "test_file_logger.log"
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "Test message" in content
