"""
Unit tests for the logging module (src.utils.logging).
"""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.logging import (
    setup_logger,
    log_progress,
    log_metric,
    log_error_summary,
    get_logger,
    StructuredFormatter,
)


class TestStructuredFormatter:
    def test_format_basic(self):
        """Test basic log formatting."""
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
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_format_with_extra_json(self):
        """Test log formatting with extra JSON data."""
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
        record.extra_json = {"key": "value", "number": 42}
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["number"] == 42


class TestSetupLogger:
    def test_console_handler_added(self):
        """Test that console handler is added."""
        logger = setup_logger("test_console")
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_file_handler_added(self):
        """Test that file handler is added when log_file is specified."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            log_path = tmp.name

        try:
            logger = setup_logger("test_file", log_file=log_path)
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

            # Write a test log
            logger.info("Test log")

            # Verify file content
            with open(log_path, "r") as f:
                content = f.read()
            assert "Test log" in content
        finally:
            Path(log_path).unlink(missing_ok=True)

    def test_json_formatting(self):
        """Test that JSON formatting is applied when use_json=True."""
        logger = setup_logger("test_json", use_json=True)
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)


class TestLogProgress:
    def test_progress_logging(self, caplog):
        """Test that progress is logged at intervals."""
        logger = setup_logger("test_progress")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            log_progress(logger, "test_task", 10, 100)
            log_progress(logger, "test_task", 20, 100)
            log_progress(logger, "test_task", 25, 100)

        # Should log at 10%, 20%, and 100% (if called)
        # At least one progress log should be present
        assert any("Progress: test_task" in record.message for record in caplog.records)

    def test_no_progress_below_threshold(self, caplog):
        """Test that progress is not logged below threshold."""
        logger = setup_logger("test_progress2")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            log_progress(logger, "test_task", 5, 100)

        # Should not log anything (5% is not a multiple of 10 and not 100)
        progress_logs = [r for r in caplog.records if "Progress: test_task" in r.message]
        assert len(progress_logs) == 0


class TestLogMetric:
    def test_metric_logging(self, caplog):
        """Test that metrics are logged correctly."""
        logger = setup_logger("test_metric")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            log_metric(logger, "accuracy", 0.95, unit="fraction")

        assert any("Metric: accuracy = 0.95" in record.message for record in caplog.records)

    def test_metric_with_context(self, caplog):
        """Test that metrics with context are logged."""
        logger = setup_logger("test_metric2")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            log_metric(
                logger,
                "loss",
                0.5,
                context={"epoch": 1, "model": "schnet"},
            )

        assert any("Metric: loss = 0.5" in record.message for record in caplog.records)


class TestLogErrorSummary:
    def test_error_logging(self, caplog):
        """Test that errors are logged with summary."""
        logger = setup_logger("test_error")
        logger.setLevel(logging.ERROR)

        try:
            1 / 0
        except ZeroDivisionError as e:
            with caplog.at_level(logging.ERROR):
                log_error_summary(logger, e)

        assert any("Error: ZeroDivisionError" in record.message for record in caplog.records)

    def test_error_with_context(self, caplog):
        """Test that errors with context are logged."""
        logger = setup_logger("test_error2")
        logger.setLevel(logging.ERROR)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            with caplog.at_level(logging.ERROR):
                log_error_summary(logger, e, context={"task": "test_task"})

        assert any("Error: ValueError" in record.message for record in caplog.records)


class TestGetLogger:
    def test_singleton_behavior(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        assert logger1 is logger2

    def test_different_names(self):
        """Test that different logger names return different instances."""
        logger1 = get_logger("test_name1")
        logger2 = get_logger("test_name2")
        assert logger1 is not logger2