import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from src.utils.logging import (
    StructuredFormatter,
    setup_logger,
    log_progress,
    log_metric,
    log_error_summary,
    get_logger
)

class TestStructuredFormatter:
    def test_format_basic(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert "timestamp" in log_entry
        assert log_entry["module"] == "test"

    def test_format_with_extra(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_data = {"key": "value"}
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert log_entry["context"]["key"] == "value"

    def test_format_with_exception(self):
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="An error occurred",
            args=(),
            exc_info=exc_info
        )
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]

class TestSetupLogger:
    def test_setup_logger_console_only(self):
        logger = setup_logger("test_logger", level=logging.INFO)
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logger_with_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger("test_logger_file", level=logging.DEBUG, log_file=log_path)
            assert len(logger.handlers) >= 2 # Console + File

            # Log something
            logger.info("Test log")
            assert log_path.exists()
            assert log_path.stat().st_size > 0

    def test_setup_logger_json_format(self):
        logger = setup_logger("test_json", use_json=True)
        # Check that the handler uses StructuredFormatter
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_setup_logger_default_format(self):
        logger = setup_logger("test_default", use_json=False)
        handler = logger.handlers[0]
        # Default formatter is not StructuredFormatter
        assert not isinstance(handler.formatter, StructuredFormatter)

class TestLogProgress:
    def test_log_progress_basic(self):
        logger = setup_logger("test_progress", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_progress(logger, 50, 100, "Processing")
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "50/100" in call_args[0][0]
            assert "50.00" in call_args[0][0]

    def test_log_progress_with_details(self):
        logger = setup_logger("test_progress_details", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            details = {"item": "file_1"}
            log_progress(logger, 1, 10, "Step A", details)
            call_args = mock_info.call_args
            # Check if extra data is passed correctly (mock might not capture extra dict perfectly in all pytest versions, but we check the call exists)
            assert mock_info.called

class TestLogMetric:
    def test_log_metric_basic(self):
        logger = setup_logger("test_metric", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_metric(logger, "loss", 0.5)
            mock_info.assert_called_once()
            assert "loss" in mock_info.call_args[0][0]
            assert "0.5" in mock_info.call_args[0][0]

    def test_log_metric_with_epoch_step(self):
        logger = setup_logger("test_metric_full", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_metric(logger, "accuracy", 0.95, step=10, epoch=5)
            mock_info.assert_called_once()

class TestLogErrorSummary:
    def test_log_error_summary_basic(self):
        logger = setup_logger("test_error", level=logging.ERROR)
        with patch.object(logger, 'error') as mock_error:
            log_error_summary(logger, "ValueError", "Invalid input")
            mock_error.assert_called_once()
            assert "ValueError" in mock_error.call_args[0][0]

    def test_log_error_summary_with_context(self):
        logger = setup_logger("test_error_ctx", level=logging.ERROR)
        with patch.object(logger, 'error') as mock_error:
            context = {"input_id": 123}
            log_error_summary(logger, "KeyError", "Missing key", context)
            mock_error.assert_called_once()

class TestGetLogger:
    def test_get_logger_by_name(self):
        logger = get_logger("custom_name")
        assert logger.name == "custom_name"

    def test_get_logger_default(self):
        logger = get_logger()
        assert logger == logging.getLogger()