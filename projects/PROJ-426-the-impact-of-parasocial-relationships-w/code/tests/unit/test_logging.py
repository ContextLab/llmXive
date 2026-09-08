"""
Unit tests for the logging module.
"""

import pytest
import logging
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logging import (
    setup_logging,
    get_logger,
    log_progress,
    log_stage_start,
    log_stage_end,
    log_error_context,
    JsonFormatter,
)


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""

    def test_format_basic_log(self):
        """Test formatting a basic log record."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["message"] == "Test message"

    def test_format_with_extra_data(self):
        """Test formatting a log record with extra data."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"task": "ingestion", "count": 100}

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["task"] == "ingestion"
        assert log_data["count"] == 100


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_creates_file(self):
        """Test that setup_logging creates the log file and directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(
                log_level="INFO",
                log_file=log_path,
                enable_json=True,
                console_output=False,
            )

            assert log_path.exists()
            assert logger is not None
            assert len(logger.handlers) > 0

    def test_setup_logging_default_path(self):
        """Test that setup_logging uses default path if none provided."""
        with patch("src.utils.logging.LOG_DIR", Path(tempfile.gettempdir())):
            logger = setup_logging(console_output=False)
            assert logger is not None

    def test_setup_logging_clears_handlers(self):
        """Test that setup_logging clears existing handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"

            # Add a dummy handler
            root = logging.getLogger()
            dummy_handler = logging.NullHandler()
            root.addHandler(dummy_handler)

            logger = setup_logging(log_file=log_path, console_output=False)

            # Should have cleared the dummy handler
            assert dummy_handler not in logger.handlers


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_with_name(self):
        """Test getting a logger with a specific name."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"

    def test_get_logger_without_name(self):
        """Test getting the root logger."""
        logger = get_logger()
        assert logger == logging.getLogger()


class TestLogProgress:
    """Tests for the log_progress function."""

    def test_log_progress_calculates_percentage(self):
        """Test that progress percentage is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                log_progress(logger, "test_task", 50, 100)

                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                assert "50.0%" in call_args

    def test_log_progress_handles_zero_total(self):
        """Test that log_progress handles zero total gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                log_progress(logger, "test_task", 10, 0)

                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                assert "0.0%" in call_args

    def test_log_progress_includes_message(self):
        """Test that log_progress includes optional message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                log_progress(logger, "test_task", 50, 100, message="Processing")

                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                assert "Processing" in call_args


class TestLogStageStart:
    """Tests for the log_stage_start function."""

    def test_log_stage_start_basic(self):
        """Test basic stage start logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                log_stage_start(logger, "DataIngestion")

                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                assert "STARTING STAGE: DataIngestion" in call_args

    def test_log_stage_start_with_details(self):
        """Test stage start logging with details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                details = {"source": "zenodo", "version": "1.0"}
                log_stage_start(logger, "DataIngestion", details)

                mock_info.assert_called_once()
                # Verify details are in extra_data
                extra_data = mock_info.call_args[1]["extra"]["extra_data"]
                assert extra_data["source"] == "zenodo"


class TestLogStageEnd:
    """Tests for the log_stage_end function."""

    def test_log_stage_end_success(self):
        """Test successful stage end logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                log_stage_end(logger, "DataIngestion", success=True, duration_seconds=120.5)

                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                assert "SUCCESS" in call_args
                assert "120.50s" in call_args

    def test_log_stage_end_failure(self):
        """Test failed stage end logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "error") as mock_error:
                log_stage_end(logger, "DataIngestion", success=False)

                mock_error.assert_called_once()
                call_args = mock_error.call_args[0][0]
                assert "FAILED" in call_args

    def test_log_stage_end_with_metrics(self):
        """Test stage end logging with metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "info") as mock_info:
                metrics = {"records_processed": 1000, "errors": 0}
                log_stage_end(logger, "DataIngestion", success=True, metrics=metrics)

                mock_info.assert_called_once()
                extra_data = mock_info.call_args[1]["extra"]["extra_data"]
                assert extra_data["metrics"]["records_processed"] == 1000


class TestLogErrorContext:
    """Tests for the log_error_context function."""

    def test_log_error_context_basic(self):
        """Test basic error context logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path, console_output=False)

            with patch.object(logger, "error") as mock_error:
                context = {"file": "data.csv", "line": 42}
                log_error_context(logger, "File not found", context)

                mock_error.assert_called_once()
                call_args = mock_error.call_args[0][0]
                assert "ERROR: File not found" in call_args

                extra_data = mock_error.call_args[1]["extra"]["extra_data"]
                assert extra_data["context"]["file"] == "data.csv"
                assert extra_data["context"]["line"] == 42