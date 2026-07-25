"""
Unit tests for logging configuration.
"""
import logging
import json
import tempfile
import os
from pathlib import Path
import pytest

from src.utils.logging import (
    JSONFormatter,
    MetricsHandler,
    get_logger,
    log_metric,
    log_metric_value,
    setup_default_loggers,
    get_default_logger,
    info,
    debug,
    warning,
    error,
    critical
)


class TestJSONFormatter:
    def test_format_basic(self):
        """Test basic log record formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["line"] == 10

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_extra(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter(include_extra=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.custom_field = "custom_value"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "extra" in data
        assert data["extra"]["custom_field"] == "custom_value"


class TestMetricsHandler:
    def test_metrics_collection(self):
        """Test that metrics are collected correctly."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            metrics_file = Path(f.name)

        try:
            handler = MetricsHandler(metrics_file)
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Metric: test_metric = 0.95",
                args=(),
                exc_info=None
            )
            record.is_metric = True
            record.metric_name = "test_metric"
            record.metric_value = 0.95

            handler.emit(record)

            metrics = handler.get_metrics()
            assert "test_metric" in metrics
            assert len(metrics["test_metric"]) == 1
            assert metrics["test_metric"][0]["value"] == 0.95
        finally:
            metrics_file.unlink(missing_ok=True)

    def test_metrics_file_save(self):
        """Test that metrics are saved to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            metrics_file = Path(f.name)

        try:
            handler = MetricsHandler(metrics_file)
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Metric: test_metric = 0.95",
                args=(),
                exc_info=None
            )
            record.is_metric = True
            record.metric_name = "test_metric"
            record.metric_value = 0.95

            handler.emit(record)
            handler._save_metrics()

            with open(metrics_file, "r") as f:
                saved_metrics = json.load(f)

            assert "test_metric" in saved_metrics
            assert saved_metrics["test_metric"][0]["value"] == 0.95
        finally:
            metrics_file.unlink(missing_ok=True)


class TestGetLogger:
    def test_logger_creation(self):
        """Test basic logger creation."""
        logger = get_logger("test_logger")
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

    def test_logger_with_file(self):
        """Test logger with file handler."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_file = Path(f.name)

        try:
            logger = get_logger("test_logger_file", log_file=log_file)
            assert len(logger.handlers) >= 2  # Console + File

            logger.info("Test message")

            # Check file has content
            with open(log_file, "r") as f:
                content = f.read()
            assert "Test message" in content
        finally:
            log_file.unlink(missing_ok=True)

    def test_logger_with_json_format(self):
        """Test logger with JSON formatting."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_file = Path(f.name)

        try:
            logger = get_logger("test_logger_json", log_file=log_file, json_format=True)

            logger.info("JSON test message")

            with open(log_file, "r") as f:
                line = f.readline()
                data = json.loads(line)

            assert data["message"] == "JSON test message"
            assert "timestamp" in data
        finally:
            log_file.unlink(missing_ok=True)


class TestLogMetric:
    def test_log_metric_function(self):
        """Test log_metric function."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            metrics_file = Path(f.name)

        try:
            logger = get_logger("test_metric_logger", metrics_file=metrics_file)
            log_metric(logger, "accuracy", 0.95)

            with open(metrics_file, "r") as f:
                metrics = json.load(f)

            assert "accuracy" in metrics
            assert metrics["accuracy"][0]["value"] == 0.95
        finally:
            metrics_file.unlink(missing_ok=True)

    def test_log_metric_value_function(self):
        """Test log_metric_value function."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            metrics_file = Path(f.name)

        try:
            logger = get_logger("test_metric_value_logger", metrics_file=metrics_file)
            log_metric_value(logger, "loss", 0.05)

            with open(metrics_file, "r") as f:
                metrics = json.load(f)

            assert "loss" in metrics
            assert metrics["loss"][0]["value"] == 0.05
        finally:
            metrics_file.unlink(missing_ok=True)


class TestSetupDefaultLoggers:
    def test_setup_default_loggers(self):
        """Test setup of default loggers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            metrics_file = Path(tmpdir) / "metrics.json"

            setup_default_loggers(log_dir=log_dir, metrics_file=metrics_file)

            logger = get_default_logger()
            assert logger is not None
            assert len(logger.handlers) >= 2

    def test_convenience_functions(self):
        """Test convenience logging functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"

            setup_default_loggers(log_dir=log_dir)

            # These should not raise
            info("Info message")
            debug("Debug message")
            warning("Warning message")
            error("Error message")
            critical("Critical message")


class TestGetDefaultLogger:
    def test_get_default_logger(self):
        """Test getting default logger."""
        logger = get_default_logger()
        assert logger is not None
        assert logger.name == "llmXive"
