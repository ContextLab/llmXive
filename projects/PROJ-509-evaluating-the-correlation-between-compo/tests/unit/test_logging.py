"""
Unit tests for the logging infrastructure.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys
# Ensure code directory is in path for imports if running from root
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import setup_logging, get_logger


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_console_handler_created(self, tmp_path):
        """Test that a console handler is always created."""
        logger = setup_logging(
            log_level="INFO",
            project_root=tmp_path
        )
        assert len(logger.handlers) >= 1
        console_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.StreamHandler)),
            None
        )
        assert console_handler is not None

    def test_file_handler_created_when_path_provided(self, tmp_path):
        """Test that a file handler is created when log_file is provided."""
        log_file = "data/logs/test.log"
        logger = setup_logging(
            log_level="DEBUG",
            log_file=log_file,
            project_root=tmp_path
        )
        
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None
        assert file_handler.baseFilename == str(tmp_path / log_file)

    def test_log_level_set_correctly(self, tmp_path):
        """Test that the logger level is set correctly."""
        logger = setup_logging(log_level="DEBUG", project_root=tmp_path)
        assert logger.level == logging.DEBUG

        logger2 = setup_logging(log_level="ERROR", project_root=tmp_path)
        assert logger2.level == logging.ERROR

    def test_log_directory_created(self, tmp_path):
        """Test that the logs directory is created if it doesn't exist."""
        log_file = "data/logs/new_subdir/test.log"
        logger = setup_logging(
            log_level="INFO",
            log_file=log_file,
            project_root=tmp_path
        )
        
        log_dir = tmp_path / "data" / "logs" / "new_subdir"
        assert log_dir.exists()

    def test_duplicate_handler_prevention(self, tmp_path):
        """Test that calling setup_logging multiple times doesn't add duplicate handlers."""
        logger = setup_logging(log_level="INFO", project_root=tmp_path)
        initial_count = len(logger.handlers)
        
        # Call again
        logger2 = setup_logging(log_level="INFO", project_root=tmp_path)
        
        # Should be the same logger instance or at least not add more handlers to the named logger
        # Since we are using a named logger 'research', we check the handlers of that name
        test_logger = logging.getLogger("research")
        assert len(test_logger.handlers) == initial_count

    def test_logger_output(self, tmp_path, caplog):
        """Test that the logger actually outputs messages."""
        logger = setup_logging(log_level="INFO", project_root=tmp_path)
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        assert "Test message" in caplog.text

class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_existing_logger(self, tmp_path):
        """Test retrieving a logger that was set up."""
        setup_logging(project_root=tmp_path)
        logger = get_logger("research")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_custom_logger(self, tmp_path):
        """Test retrieving a custom named logger."""
        setup_logging(project_root=tmp_path)
        custom_logger = get_logger("custom_module")
        assert custom_logger.name == "custom_module"