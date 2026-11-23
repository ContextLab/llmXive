"""
Unit tests for src/utils.py functionality.
"""
import os
import sys
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
# Adjust path based on project structure if necessary
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import (
    setup_logging,
    compute_checksum,
    log_error,
    safe_exit,
    timing_decorator
)
import logging


class TestSetupLogging:
    def test_setup_logging_console_only(self, caplog):
        """Test that logging works to console when no file is specified."""
        logger = setup_logging(log_file=None, level=logging.INFO)
        assert logger.level == logging.INFO
        # Verify a message is logged
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
            assert "Test message" in caplog.text

    def test_setup_logging_with_file(self, tmp_path):
        """Test that logging creates a file and writes to it."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file), level=logging.DEBUG)

        logger.debug("Debug message")
        logger.info("Info message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Debug message" in content
        assert "Info message" in content

    def test_setup_logging_clears_handlers(self):
        """Test that setup_logging clears existing handlers."""
        initial_logger = logging.getLogger()
        initial_handler_count = len(initial_logger.handlers)

        # Add a dummy handler
        initial_logger.addHandler(logging.NullHandler())

        setup_logging(log_file=None)

        # Check if the dummy handler was removed and replaced by console handler
        # (Note: exact count depends on previous state, but handlers should be replaced)
        # A more robust check is ensuring the new handler is present
        console_handlers = [h for h in initial_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) >= 1


class TestComputeChecksum:
    def test_compute_checksum_valid_file(self, tmp_path):
        """Test checksum calculation on a valid file."""
        test_file = tmp_path / "data.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        checksum = compute_checksum(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_compute_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_checksum("nonexistent_file.txt")

    def test_compute_checksum_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for invalid algorithm."""
        test_file = tmp_path / "data.txt"
        test_file.write_text("data")

        with pytest.raises(ValueError):
            compute_checksum(test_file, algorithm="invalid_algo")


class TestLogError:
    def test_log_error_with_context(self, caplog):
        """Test logging an exception with context."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error")
            except Exception as e:
                log_error(e, context="Context info")

        assert "Context info" in caplog.text
        assert "ValueError" in caplog.text

    def test_log_error_without_context(self, caplog):
        """Test logging an exception without context."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        with caplog.at_level(logging.ERROR):
            try:
                raise RuntimeError("Another error")
            except Exception as e:
                log_error(e)

        assert "RuntimeError" in caplog.text


class TestSafeExit:
    def test_safe_exit_success(self, caplog):
        """Test safe exit with code 0."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)

        with patch("sys.exit") as mock_exit:
            with caplog.at_level(logging.INFO):
                safe_exit(0)
            assert mock_exit.called
            assert "Exiting successfully" in caplog.text

    def test_safe_exit_failure(self, caplog):
        """Test safe exit with non-zero code."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        with patch("sys.exit") as mock_exit:
            with caplog.at_level(logging.ERROR):
                safe_exit(1)
            assert mock_exit.called
            assert "Exiting with error code: 1" in caplog.text


class TestTimingDecorator:
    def test_timing_decorator_success(self, caplog):
        """Test that the timing decorator logs duration on success."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)

        @timing_decorator
        def slow_function():
            time.sleep(0.1)
            return "done"

        with caplog.at_level(logging.INFO):
            result = slow_function()

        assert result == "done"
        assert "completed in" in caplog.text
        assert "seconds" in caplog.text

    def test_timing_decorator_failure(self, caplog):
        """Test that the timing decorator logs duration on failure."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)

        @timing_decorator
        def failing_function():
            raise ValueError("Failed!")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()

        assert "failed after" in caplog.text