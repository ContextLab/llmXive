"""
Unit tests for the logging configuration module.
"""

import logging
import os
import tempfile
from pathlib import Path
import pytest

from utils.logging_config import (
    setup_logging,
    get_logger,
    configure_module_logger,
    get_module_logger,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_DIR,
)


class TestLoggingSetup:
    """Tests for logging setup functionality."""

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that setup_logging creates console and file handlers."""
        log_dir = tmp_path / "logs"
        setup_logging(
            log_level=logging.DEBUG,
            log_dir=str(log_dir),
            enable_console_logging=True,
            enable_file_logging=True,
        )

        root_logger = logging.getLogger()
        handlers = root_logger.handlers

        assert len(handlers) >= 2, "Should have at least console and file handlers"

        # Check for RotatingFileHandler
        file_handlers = [h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) > 0, "Should have a rotating file handler"

    def test_setup_logging_creates_log_directory(self, tmp_path):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        log_dir = tmp_path / "nonexistent" / "logs"
        setup_logging(
            log_dir=str(log_dir),
            enable_console_logging=False,
            enable_file_logging=True,
        )

        assert log_dir.exists(), "Log directory should be created"

    def test_setup_logging_sets_level(self, tmp_path):
        """Test that setup_logging sets the correct log level."""
        log_dir = tmp_path / "logs"
        setup_logging(
            log_level=logging.WARNING,
            log_dir=str(log_dir),
            enable_console_logging=False,
            enable_file_logging=False,
        )

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_setup_logging_no_file_logging(self, tmp_path):
        """Test setup_logging with only console logging."""
        log_dir = tmp_path / "logs"
        setup_logging(
            log_dir=str(log_dir),
            enable_console_logging=True,
            enable_file_logging=False,
        )

        root_logger = logging.getLogger()
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) == 0, "Should have no file handlers"


class TestGetLogger:
    """Tests for get_logger functionality."""

    def test_get_logger_root(self):
        """Test that get_logger returns root logger when name is None."""
        logger = get_logger()
        assert logger.name == "root"

    def test_get_logger_creates_named_logger(self):
        """Test that get_logger creates a named logger."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"

    def test_get_logger_caching(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("cached.module")
        logger2 = get_logger("cached.module")
        assert logger1 is logger2

    def test_get_logger_propagation(self):
        """Test that child loggers propagate to root."""
        logger = get_logger("propagate.test")
        assert logger.propagate is True


class TestConfigureModuleLogger:
    """Tests for configure_module_logger functionality."""

    def test_configure_module_logger_sets_level(self, tmp_path):
        """Test that configure_module_logger sets the correct level."""
        setup_logging(
            log_level=logging.INFO,
            log_dir=str(tmp_path / "logs"),
            enable_console_logging=False,
            enable_file_logging=False,
        )

        logger = configure_module_logger("test.module", log_level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_configure_module_logger_without_level(self, tmp_path):
        """Test that configure_module_logger uses default level when not specified."""
        setup_logging(
            log_level=logging.WARNING,
            log_dir=str(tmp_path / "logs"),
            enable_console_logging=False,
            enable_file_logging=False,
        )

        logger = configure_module_logger("test.module")
        # Should inherit from root or be NOTSET
        assert logger.level in (logging.NOTSET, logging.WARNING)


class TestModuleLogger:
    """Tests for get_module_logger functionality."""

    def test_get_module_logger_returns_logger(self):
        """Test that get_module_logger returns a valid logger."""
        logger = get_module_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name is not None
