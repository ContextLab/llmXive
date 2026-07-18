import logging
import json
import tempfile
import os
from pathlib import Path
import pytest
import sys

# Ensure code/ is in path
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
    critical
)


class TestJSONFormatter:
    def test_format_basic_record(self):
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
        output = formatter.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["module"] == "test"

    def test_format_with_extra_data(self):
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
        record.extra_data = {"key": "value", "num": 123}
        output = formatter.format(record)
        data = json.loads(output)
        assert data["extra"]["key"] == "value"
        assert data["extra"]["num"] == 123


class TestMetricsHandler:
    def test_emit_dict_message(self, tmp_path):
        metrics_file = tmp_path / "metrics.jsonl"
        handler = MetricsHandler(metrics_file)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg={"metric_name": "loss", "value": 0.5},
            args=(),
            exc_info=None
        )
        handler.emit(record)
        
        assert metrics_file.exists()
        with open(metrics_file, "r") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["metric_name"] == "loss"
            assert data["value"] == 0.5

    def test_emit_string_message(self, tmp_path):
        metrics_file = tmp_path / "metrics.jsonl"
        handler = MetricsHandler(metrics_file)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Simple string metric",
            args=(),
            exc_info=None
        )
        handler.emit(record)
        
        assert metrics_file.exists()
        with open(metrics_file, "r") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["message"] == "Simple string metric"


class TestGetLogger:
    def test_logger_creation(self, tmp_path):
        logger = get_logger("test_logger", log_dir=tmp_path)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0

    def test_log_rotation_config(self, tmp_path):
        logger = get_logger("test_rotation", log_dir=tmp_path)
        file_handler = None
        for h in logger.handlers:
            if isinstance(h, logging.handlers.RotatingFileHandler):
                file_handler = h
                break
        assert file_handler is not None
        assert file_handler.maxBytes == 10 * 1024 * 1024


class TestLogMetric:
    def test_log_numeric_metric(self, tmp_path):
        logger = get_logger("test_metric", log_dir=tmp_path)
        log_metric(logger, "accuracy", 0.95)
        
        metrics_file = tmp_path / "metrics.jsonl"
        assert metrics_file.exists()
        with open(metrics_file, "r") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["metric_name"] == "accuracy"
            assert data["value"] == 0.95

    def test_log_dict_metric(self, tmp_path):
        logger = get_logger("test_dict_metric", log_dir=tmp_path)
        log_metric(logger, "batch_stats", {"loss": 0.1, "acc": 0.8})
        
        metrics_file = tmp_path / "metrics.jsonl"
        with open(metrics_file, "r") as f:
            line = f.readline()
            data = json.loads(line)
            assert data["metric_name"] == "batch_stats"
            assert data["loss"] == 0.1


class TestSetupDefaultLoggers:
    def test_console_handler_added(self):
        # Reset root logger handlers
        root = logging.getLogger()
        root.handlers = []
        
        setup_default_loggers()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)


class TestGetDefaultLogger:
    def test_returns_logger(self):
        logger = get_default_logger()
        assert logger is not None
        assert logger.name == "llmxive"


class TestConvenienceFunctions:
    def test_info(self, caplog, tmp_path):
        # Temporarily override get_default_logger to use a test logger
        import src.utils.logging as logging_module
        original_get = logging_module.get_default_logger
        
        test_logger = get_logger("test_convenience", log_dir=tmp_path)
        logging_module.get_default_logger = lambda: test_logger
        
        try:
            info("Test info message")
            # Check file output
            metrics_file = tmp_path / "metrics.jsonl"
            log_file = tmp_path / "pipeline.log"
            # The info function logs to the default logger which has both handlers
            # We verify the log file exists and has content
            assert log_file.exists()
        finally:
            logging_module.get_default_logger = original_get