"""
Unit tests for src.utils.logging module.
"""
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
    get_logger,
    LOG_DIR,
)


class TestStructuredFormatter:
    def test_format_basic(self):
        """Test basic log record formatting."""
        formatter = StructuredFormatter()
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
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_format_with_extra_data(self):
        """Test formatting with extra data."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value", "number": 42}
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["number"] == 42

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="An error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            output = formatter.format(record)
            parsed = json.loads(output)

            assert parsed["level"] == "ERROR"
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]


class TestSetupLogger:
    def test_setup_logger_console_only(self):
        """Test logger setup with console output only."""
        logger = setup_logger("test_console", level=logging.INFO, use_json=True)
        assert logger.name == "test_console"
        assert len(logger.handlers) == 1  # Console handler
        assert isinstance(logger.handlers[0].formatter, StructuredFormatter)

    def test_setup_logger_with_file(self):
        """Test logger setup with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logger("test_file", log_file=log_file, use_json=True)

            assert len(logger.handlers) == 2  # Console + File
            logger.info("Test log message")

            assert log_file.exists()
            with open(log_file, "r") as f:
                content = f.read()
                parsed = json.loads(content.strip())
                assert parsed["message"] == "Test log message"

    def test_setup_logger_reuse(self):
        """Test that calling setup_logger again doesn't add duplicate handlers."""
        logger = setup_logger("test_reuse", level=logging.INFO)
        initial_count = len(logger.handlers)
        logger2 = setup_logger("test_reuse", level=logging.DEBUG)
        assert len(logger2.handlers) == initial_count


class TestLogProgress:
    def test_log_progress_basic(self):
        """Test basic progress logging."""
        logger = setup_logger("test_progress", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_progress(logger, "data_ingestion", 50, 100)
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "data_ingestion" in call_args
            assert "50/100" in call_args
            assert "50.0%" in call_args

    def test_log_progress_with_message(self):
        """Test progress logging with custom message."""
        logger = setup_logger("test_progress_msg", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_progress(logger, "model_training", 10, 50, message="Epoch 10 complete")
            call_args = mock_info.call_args[0][0]
            assert "Epoch 10 complete" in call_args


class TestLogMetric:
    def test_log_metric_basic(self):
        """Test basic metric logging."""
        logger = setup_logger("test_metric", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_metric(logger, "loss", 0.543)
            call_args = mock_info.call_args[0][0]
            assert "loss" in call_args
            assert "0.543" in call_args

    def test_log_metric_with_unit(self):
        """Test metric logging with unit."""
        logger = setup_logger("test_metric_unit", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_metric(logger, "accuracy", 0.95, unit="%")
            call_args = mock_info.call_args[0][0]
            assert "%" in call_args

    def test_log_metric_with_step(self):
        """Test metric logging with step."""
        logger = setup_logger("test_metric_step", level=logging.INFO)
        with patch.object(logger, 'info') as mock_info:
            log_metric(logger, "loss", 0.5, step=10)
            call_args = mock_info.call_args[0][0]
            assert "step 10" in call_args


class TestLogErrorSummary:
    def test_log_error_basic(self):
        """Test basic error summary logging."""
        logger = setup_logger("test_error", level=logging.ERROR)
        with patch.object(logger, 'error') as mock_error:
            log_error_summary(logger, "ValueError", "Invalid input")
            call_args = mock_error.call_args[0][0]
            assert "ValueError" in call_args
            assert "Invalid input" in call_args

    def test_log_error_with_context(self):
        """Test error summary logging with context."""
        logger = setup_logger("test_error_ctx", level=logging.ERROR)
        with patch.object(logger, 'error') as mock_error:
            context = {"input_shape": (3, 224, 224), "expected": 2}
            log_error_summary(logger, "RuntimeError", "Shape mismatch", context=context)
            assert mock_error.called


class TestGetLogger:
    def test_get_logger_default(self):
        """Test getting default logger."""
        logger = get_logger()
        assert logger.name == "llmXive"
        assert len(logger.handlers) > 0

    def test_get_logger_custom_name(self):
        """Test getting logger with custom name."""
        logger = get_logger("custom_name")
        assert logger.name == "custom_name"