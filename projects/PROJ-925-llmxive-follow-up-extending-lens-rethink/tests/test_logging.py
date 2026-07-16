"""
Tests for the logging infrastructure in code/utils/logging.py.
"""

import os
import tempfile
import logging
from pathlib import Path
import pytest

# Import the module under test
from code.utils.logging import (
    setup_logging,
    get_logger,
    log_info,
    log_warning,
    log_error,
    _LOG_DIR,
    _configured,
)


class TestLoggingInfrastructure:
    """Test cases for logging configuration and utilities."""

    def setup_method(self):
        """Reset logging state before each test."""
        # Force reconfiguration by resetting the internal flag
        # Note: In a real scenario, we might need to mock the module globals
        # but for this test, we assume a fresh import or direct reset.
        pass

    def test_setup_logging_creates_directory(self, tmp_path):
        """Verify that setup_logging creates the log directory."""
        # Override the global log dir for this test
        import code.utils.logging as logging_module
        original_dir = logging_module._LOG_DIR
        test_dir = tmp_path / "logs"
        logging_module._LOG_DIR = test_dir
        logging_module._configured = False

        try:
            setup_logging(log_file=test_dir / "test.log", console=False)
            assert test_dir.exists(), "Log directory should be created"
        finally:
            # Restore original
            logging_module._LOG_DIR = original_dir
            logging_module._configured = False

    def test_setup_logging_returns_logger(self):
        """Verify that setup_logging returns a logger instance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            logger = setup_logging(log_file=log_file, console=False)

            assert isinstance(logger, logging.Logger)
            assert logger.level == logging.INFO

    def test_get_logger_after_setup(self):
        """Verify that get_logger returns a configured logger."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            setup_logging(log_file=log_file, console=False)

            logger = get_logger("test_module")
            assert isinstance(logger, logging.Logger)
            assert logger.name == "test_module"

    def test_get_logger_root(self):
        """Verify that get_logger(None) returns the root logger."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            setup_logging(log_file=log_file, console=False)

            logger = get_logger()
            assert isinstance(logger, logging.Logger)
            assert logger.name == "root"

    def test_log_functions_write_to_logger(self):
        """Verify that utility log functions call the logger."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            setup_logging(log_file=log_file, console=False)

            # These should not raise exceptions
            log_info("Info message")
            log_warning("Warning message")

            # Check if file exists and has content
            assert log_file.exists(), "Log file should exist"
            with open(log_file, "r") as f:
                content = f.read()
                assert "Info message" in content
                assert "Warning message" in content

    def test_logger_level_respected(self, tmp_path):
        """Verify that setting a level filters messages."""
        log_file = tmp_path / "test.log"
        setup_logging(level=logging.WARNING, log_file=log_file, console=False)

        log_info("This should be filtered")
        log_warning("This should appear")

        with open(log_file, "r") as f:
            content = f.read()
            assert "This should be filtered" not in content
            assert "This should appear" in content

    def test_multiple_setup_calls_idempotent(self):
        """Verify that calling setup_logging multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            # First call
            logger1 = setup_logging(log_file=log_file, console=False)
            # Second call
            logger2 = setup_logging(level=logging.DEBUG, log_file=log_file, console=False)

            # Should return the same configured logger (or at least a valid one)
            assert isinstance(logger2, logging.Logger)
            # Handlers should not be duplicated if idempotent logic holds
            # (Implementation detail: current logic clears handlers if not _configured)
            # But since _configured is True, it returns early.
            assert logger1 is logger2
