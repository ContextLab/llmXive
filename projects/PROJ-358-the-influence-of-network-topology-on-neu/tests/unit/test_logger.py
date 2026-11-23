"""
Unit tests for the logging infrastructure.
"""

import logging
import os
import tempfile
from pathlib import Path
import pytest

import sys
# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logger import setup_logging, get_logger, get_project_root


class TestLoggerSetup:
    """Tests for logging setup functionality."""

    def test_setup_logging_creates_handlers(self):
        """Verify that setup_logging creates console and file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(
                log_dir=tmpdir,
                log_file="test.log",
                console=True,
                file=True,
            )

            # Check handlers exist
            assert len(logger.handlers) == 2

            # Check handler types
            handler_types = [type(h).__name__ for h in logger.handlers]
            assert "StreamHandler" in handler_types
            assert "RotatingFileHandler" in handler_types

    def test_setup_logging_creates_log_file(self):
        """Verify that setup_logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file_name = "test.log"
            setup_logging(
                log_dir=tmpdir,
                log_file=log_file_name,
                console=False,
                file=True,
            )

            log_path = Path(tmpdir) / log_file_name
            assert log_path.exists()

    def test_setup_logging_sets_level(self):
        """Verify that setup_logging sets the correct log level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(
                log_level=logging.DEBUG,
                log_dir=tmpdir,
                log_file="test.log",
            )

            assert logger.level == logging.DEBUG

    def test_get_logger_returns_configured_logger(self):
        """Verify that get_logger returns a properly configured logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                log_dir=tmpdir,
                log_file="test.log",
            )

            logger = get_logger("test_module")

            assert isinstance(logger, logging.Logger)
            assert logger.name == "test_module"

    def test_get_logger_propagates_to_root(self):
        """Verify that child loggers propagate to root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                log_dir=tmpdir,
                log_file="test.log",
            )

            logger = get_logger("parent.child")
            assert logger.propagate is True

    def test_log_message_writes_to_file(self, tmp_path):
        """Verify that logging a message writes to the log file."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        logger = setup_logging(
            log_dir=str(log_dir),
            log_file=log_file,
            console=False,
        )

        test_message = "Test log message"
        logger.info(test_message)

        log_path = log_dir / log_file
        assert log_path.exists()

        content = log_path.read_text()
        assert test_message in content

    def test_rotating_file_handler_respects_backup_count(self, tmp_path):
        """Verify that RotatingFileHandler respects backup count."""
        log_dir = tmp_path / "logs"
        log_file = "rotating.log"
        max_bytes = 1024  # 1 KB for testing
        backup_count = 3

        logger = setup_logging(
            log_dir=str(log_dir),
            log_file=log_file,
            max_bytes=max_bytes,
            backup_count=backup_count,
            console=False,
        )

        # Write enough data to trigger rotation
        test_message = "X" * 500  # 500 bytes per message
        for _ in range(10):
            logger.info(test_message)

        log_path = log_dir / log_file
        backup_files = list(log_dir.glob(f"{log_file}.*"))

        # Should not exceed backup_count
        assert len(backup_files) <= backup_count

    def test_get_project_root_returns_path(self):
        """Verify that get_project_root returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
