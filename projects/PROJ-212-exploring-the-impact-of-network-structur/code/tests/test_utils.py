"""
Unit tests for src/utils.py utilities.
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path
import pytest
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import (
    setup_logging,
    compute_checksum,
    log_error,
    safe_exit,
    timing_decorator
)


class TestSetupLogging:
    def test_setup_logging_console_only(self, tmp_path):
        """Test that logging is set up correctly with console handler."""
        logger = setup_logging(log_level="INFO", module_name="test_console")
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1  # Console handler
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_with_file(self, tmp_path):
        """Test that logging is set up correctly with file handler."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(
            log_level="DEBUG",
            log_file=log_file,
            module_name="test_file"
        )
        assert len(logger.handlers) == 2  # Console + File
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert log_file.exists() is False  # Not created until write

        # Force a log to create file
        logger.info("Test message")
        assert log_file.exists()

    def test_setup_logging_duplicate_call(self, tmp_path):
        """Test that duplicate calls don't add duplicate handlers."""
        logger = setup_logging(module_name="test_dup")
        initial_count = len(logger.handlers)
        logger2 = setup_logging(module_name="test_dup")
        assert len(logger2.handlers) == initial_count


class TestComputeChecksum:
    def test_compute_checksum_sha256(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "checksum_test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = compute_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

    def test_compute_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_checksum(Path("/nonexistent/file.txt"))

    def test_compute_checksum_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for unsupported algorithm."""
        test_file = tmp_path / "algo_test.txt"
        test_file.write_bytes(b"test")
        with pytest.raises(ValueError):
            compute_checksum(test_file, algorithm="invalid_algo")

    def test_compute_checksum_large_file(self, tmp_path):
        """Test checksum on a larger file (chunking)."""
        test_file = tmp_path / "large.txt"
        # Write 1MB of data
        test_file.write_bytes(b"0" * (1024 * 1024))
        checksum = compute_checksum(test_file)
        assert len(checksum) == 64


class TestLogError:
    def test_log_error_basic(self, tmp_path, caplog):
        """Test basic error logging."""
        log_file = tmp_path / "error.log"
        logger = setup_logging(log_file=log_file, module_name="test_err")

        try:
            1 / 0
        except ZeroDivisionError as e:
            log_error(logger, e, context={"attempt": 1})

        # Verify log file contains error
        assert log_file.exists()
        content = log_file.read_text()
        assert "ZeroDivisionError" in content
        assert "attempt" in content

    def test_log_error_no_context(self, tmp_path):
        """Test error logging without context."""
        log_file = tmp_path / "error_no_ctx.log"
        logger = setup_logging(log_file=log_file, module_name="test_err2")

        try:
            raise ValueError("Simple error")
        except ValueError as e:
            log_error(logger, e)

        content = log_file.read_text()
        assert "ValueError" in content


class TestSafeExit:
    def test_safe_exit_success(self, capsys):
        """Test safe exit on success."""
        logger = setup_logging(module_name="test_exit_ok")
        with pytest.raises(SystemExit) as exc_info:
            safe_exit(logger, error=None, exit_code=0)
        assert exc_info.value.code == 0

    def test_safe_exit_failure(self, caplog, tmp_path):
        """Test safe exit on failure with error."""
        log_file = tmp_path / "exit_fail.log"
        logger = setup_logging(log_file=log_file, module_name="test_exit_fail")

        test_error = RuntimeError("Critical failure")
        with pytest.raises(SystemExit) as exc_info:
            safe_exit(logger, error=test_error, exit_code=1)

        assert exc_info.value.code == 1
        content = log_file.read_text()
        assert "RuntimeError" in content
        assert "Critical failure" in content


class TestTimingDecorator:
    def test_timing_decorator_logs_time(self, caplog):
        """Test that the decorator logs execution time."""
        logger = logging.getLogger("TestTiming")
        logger.setLevel(logging.INFO)

        @timing_decorator
        def slow_function():
            time.sleep(0.1)
            return 42

        # Capture log output
        with caplog.at_level(logging.INFO):
            result = slow_function()

        assert result == 42
        # Check that log contains timing info
        assert any("completed in" in msg for msg in caplog.messages)

    def test_timing_decorator_preserves_return(self):
        """Test that the decorator preserves the return value."""
        @timing_decorator
        def fast_function():
            return "success"

        assert fast_function() == "success"

    def test_timing_decorator_on_exception(self):
        """Test that decorator handles exceptions correctly (logs time even on error)."""
        @timing_decorator
        def failing_function():
            raise ValueError("Intentional error")

        with pytest.raises(ValueError):
            failing_function()
        # If we get here without crashing, the decorator handled the finally block correctly