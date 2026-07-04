"""
Unit tests for the logging infrastructure in src/utils/logging.py.

These tests verify that:
1. Loggers are created with the correct level.
2. Handlers (console and file) are attached correctly.
3. Log files are created in the expected location.
4. The logger respects environment variables for log levels.
"""

import logging
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from src.utils.logging import (
    setup_logging,
    get_logger,
    init_logging,
    _get_log_level,
)
from src.utils.config import get_project_root


class TestLoggingInfrastructure:
    """Tests for the logging setup and retrieval functions."""

    def test_setup_logging_creates_logger(self):
        """Verify that setup_logging returns a configured logger."""
        logger = setup_logging(name="test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0

    def test_setup_logging_adds_console_handler(self):
        """Verify that a StreamHandler is added for console output."""
        logger = setup_logging(name="test_console", file=False)
        handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) == 1

    def test_setup_logging_adds_file_handler(self):
        """Verify that a FileHandler is added for file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(name="test_file", log_file=str(log_path), console=False)
            handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(handlers) == 1
            # Verify the file was created
            assert log_path.exists()

    def test_log_level_defaults_to_info(self):
        """Verify default log level is INFO when no env vars are set."""
        # Ensure DEBUG env var is not set
        old_debug = os.environ.pop("DEBUG", None)
        old_level = os.environ.pop("LOG_LEVEL", None)

        try:
            level = _get_log_level()
            assert level.upper() == "INFO"
        finally:
            # Restore environment
            if old_debug is not None:
                os.environ["DEBUG"] = old_debug
            if old_level is not None:
                os.environ["LOG_LEVEL"] = old_level

    def test_log_level_respects_debug_env(self):
        """Verify log level is DEBUG when DEBUG=true."""
        os.environ["DEBUG"] = "true"
        try:
            level = _get_log_level()
            assert level.upper() == "DEBUG"
        finally:
            os.environ.pop("DEBUG", None)

    def test_log_level_respects_log_level_env(self):
        """Verify log level respects LOG_LEVEL environment variable."""
        os.environ["LOG_LEVEL"] = "WARNING"
        try:
            level = _get_log_level()
            assert level.upper() == "WARNING"
        finally:
            os.environ.pop("LOG_LEVEL", None)

    def test_get_logger_lazy_initialization(self):
        """Verify get_logger initializes logging if not already set up."""
        # Reset global state by removing handlers from root if necessary
        # (In a real test suite, we might mock or reset more aggressively)
        logger = get_logger(name="lazy_test")
        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) > 0

    def test_init_logging(self):
        """Verify init_logging sets up the default logger."""
        logger = init_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive_pipeline"

    def test_logger_output_to_file(self):
        """Verify that logging messages are written to the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "output_test.log"
            logger = setup_logging(
                name="output_test",
                log_file=str(log_path),
                console=False,
                level="DEBUG"
            )
            
            logger.debug("Test debug message")
            logger.info("Test info message")
            logger.warning("Test warning message")

            # Read file content
            content = log_path.read_text()
            
            assert "Test debug message" in content
            assert "Test info message" in content
            assert "Test warning message" in content
            assert "DEBUG" in content
            assert "INFO" in content
            assert "WARNING" in content

    def test_logger_handles_special_characters(self):
        """Verify logging handles unicode and special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "unicode_test.log"
            logger = setup_logging(
                name="unicode_test",
                log_file=str(log_path),
                console=False,
                level="INFO"
            )
            
            test_msg = "Test with unicode: 你好世界 🚀"
            logger.info(test_msg)

            content = log_path.read_text()
            assert test_msg in content

    def test_multiple_calls_to_setup_logging(self):
        """Verify that calling setup_logging multiple times doesn't duplicate handlers."""
        logger = setup_logging(name="multi_call", console=False)
        initial_count = len(logger.handlers)
        
        # Call again
        logger2 = setup_logging(name="multi_call", console=False)
        
        # Should be the same logger instance or at least same handler count
        assert len(logger2.handlers) == initial_count
        assert logger is logger2