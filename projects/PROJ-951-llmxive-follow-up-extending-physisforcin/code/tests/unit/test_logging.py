"""
Unit tests for the logging configuration module.
"""
import logging
import json
import tempfile
import os
from pathlib import Path
import pytest
import sys

# Import the module under test
# Adjust import path based on project structure
try:
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
        critical,
        main,
    )
except ImportError:
    # Fallback for direct execution in tests directory if path is not set up
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
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
        critical,
        main,
    )


class TestJSONFormatter:
    def test_format_basic(self):
        formatter = JSONFormatter()
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
        data = json.loads(output)
        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test"

    def test_format_with_exception(self):
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
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_metrics(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Metric update",
            args=(),
            exc_info=None,
        )
        record.metrics = {"loss": 0.5}
        output = formatter.format(record)
        data = json.loads(output)
        assert "metrics" in data
        assert data["metrics"]["loss"] == 0.5


class TestMetricsHandler:
    def test_emit_metric(self):
        store = {}
        handler = MetricsHandler(store)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Metric",
            args=(),
            exc_info=None,
        )
        record.metrics = {"accuracy": 0.9}
        record.metric_name = "accuracy"

        handler.emit(record)

        assert "accuracy" in store
        assert len(store["accuracy"]) == 1
        assert store["accuracy"][0]["accuracy"] == 0.9

    def test_emit_no_metrics(self):
        store = {}
        handler = MetricsHandler(store)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Info",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        assert store == {}


class TestGetLogger:
    def test_console_handler_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_console", log_dir=tmpdir)
            assert len(logger.handlers) >= 1
            # Check for StreamHandler
            has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
            assert has_stream

    def test_file_handler_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger(
                "test_file", log_file="test.log", log_dir=tmpdir
            )
            assert len(logger.handlers) >= 2  # Console + File
            has_file = any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers)
            assert has_file

            # Verify file exists
            log_path = Path(tmpdir) / "test.log"
            assert log_path.exists()

    def test_json_formatter_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger(
                "test_json", log_file="test.jsonl", log_dir=tmpdir, json_logging=True
            )
            file_handler = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)][0]
            assert isinstance(file_handler.formatter, JSONFormatter)

    def test_no_duplicate_handlers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_dup", log_dir=tmpdir)
            initial_count = len(logger.handlers)
            # Call again with same name
            logger2 = get_logger("test_dup", log_dir=tmpdir)
            # Should clear and re-add, so count remains same
            assert len(logger2.handlers) == initial_count


class TestLogMetric:
    def test_log_metric_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_metric", log_dir=tmpdir, level=logging.INFO)
            # Capture log output by adding a custom handler
            logs = []

            class CaptureHandler(logging.Handler):
                def emit(self, record):
                    logs.append(record)

            capture = CaptureHandler()
            logger.addHandler(capture)

            log_metric(logger, "loss", 0.5, step=1, metadata={"batch": 1})

            assert len(logs) == 1
            assert logs[0].metrics["name"] == "loss"
            assert logs[0].metrics["value"] == 0.5
            assert logs[0].metrics["step"] == 1
            assert logs[0].metrics["metadata"]["batch"] == 1

class TestLogMetricValue:
    def test_log_metric_value_functionality(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_metric_val", log_dir=tmpdir, level=logging.INFO)
            logs = []

            class CaptureHandler(logging.Handler):
                def emit(self, record):
                    logs.append(record)

            capture = CaptureHandler()
            logger.addHandler(capture)

            log_metric_value(logger, "accuracy", 0.9, step=2)

            assert len(logs) == 1
            assert logs[0].metrics["name"] == "accuracy"
            assert logs[0].metrics["value"] == 0.9
            assert logs[0].metrics["step"] == 2


class TestSetupDefaultLoggers:
    def test_creates_log_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_default_loggers(project_root=tmpdir)
            log_dir = Path(tmpdir) / "logs"
            assert log_dir.exists()

    def test_returns_logger(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_default_loggers(project_root=tmpdir)
            assert isinstance(logger, logging.Logger)
            assert logger.name == "llmXive"

    def test_creates_metrics_logger(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _ = setup_default_loggers(project_root=tmpdir)
            metrics_logger = logging.getLogger("llmXive.metrics")
            assert isinstance(metrics_logger, logging.Logger)
            assert metrics_logger.handlers  # Should have handlers


class TestGetDefaultLogger:
    def test_returns_logger(self):
        # Ensure setup is called first or rely on root
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_default_loggers(project_root=tmpdir)
            logger = get_default_logger()
            assert isinstance(logger, logging.Logger)
            assert logger.name == "llmXive"


class TestConvenienceFunctions:
    def test_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_info", log_dir=tmpdir)
            logs = []
            class CaptureHandler(logging.Handler):
                def emit(self, record): logs.append(record)
            logger.addHandler(CaptureHandler())

            info(logger, "Info message")
            assert len(logs) == 1
            assert logs[0].levelname == "INFO"
            assert logs[0].getMessage() == "Info message"

    def test_debug(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_debug", log_dir=tmpdir, level=logging.DEBUG)
            logs = []
            class CaptureHandler(logging.Handler):
                def emit(self, record): logs.append(record)
            logger.addHandler(CaptureHandler())

            debug(logger, "Debug message")
            assert len(logs) == 1
            assert logs[0].levelname == "DEBUG"

    def test_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_warn", log_dir=tmpdir)
            logs = []
            class CaptureHandler(logging.Handler):
                def emit(self, record): logs.append(record)
            logger.addHandler(CaptureHandler())

            warning(logger, "Warning message")
            assert len(logs) == 1
            assert logs[0].levelname == "WARNING"

    def test_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_err", log_dir=tmpdir)
            logs = []
            class CaptureHandler(logging.Handler):
                def emit(self, record): logs.append(record)
            logger.addHandler(CaptureHandler())

            error(logger, "Error message")
            assert len(logs) == 1
            assert logs[0].levelname == "ERROR"

    def test_critical(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_logger("test_crit", log_dir=tmpdir)
            logs = []
            class CaptureHandler(logging.Handler):
                def emit(self, record): logs.append(record)
            logger.addHandler(CaptureHandler())

            critical(logger, "Critical message")
            assert len(logs) == 1
            assert logs[0].levelname == "CRITICAL"


def test_convenience_functions():
    # Simple smoke test to ensure they don't crash
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = get_logger("test_smoke", log_dir=tmpdir)
        info(logger, "Test")
        debug(logger, "Test")
        warning(logger, "Test")
        error(logger, "Test")
        critical(logger, "Test")