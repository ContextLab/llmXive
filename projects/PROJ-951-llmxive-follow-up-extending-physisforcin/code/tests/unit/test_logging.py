"""
Unit tests for logging configuration.
"""
import logging
import json
import tempfile
import os
from pathlib import Path
import pytest
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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
        formatter = JSONFormatter()
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
        log_data = json.loads(output)
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
        assert log_data["logger"] == "test"

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
            exc_info=exc_info
        )
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]

class TestMetricsHandler:
    def test_emit_metric(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_file = Path(tmpdir) / "metrics.jsonl"
            handler = MetricsHandler(str(metrics_file))
            handler.setLevel(logging.INFO)
            
            formatter = JSONFormatter()
            handler.setFormatter(formatter)
            
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="METRIC: accuracy = 0.95",
                args=(),
                exc_info=None
            )
            record.extra_data = {"metric_name": "accuracy", "metric_value": 0.95}
            
            handler.emit(record)
            handler.close()
            
            assert metrics_file.exists()
            with open(metrics_file, "r") as f:
                line = f.readline()
                log_data = json.loads(line)
                assert log_data["metric_name"] == "accuracy"
                assert log_data["metric_value"] == 0.95

class TestGetLogger:
    def test_logger_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = get_logger("test_get_logger", log_file=str(log_file))
            
            assert logger is not None
            assert logger.name == "test_get_logger"
            assert len(logger.handlers) > 0
            
            # Check that log file was created
            logger.info("Test message")
            assert log_file.exists()

    def test_logger_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "rotation_test.log"
            logger = get_logger(
                "test_rotation",
                log_file=str(log_file),
                max_bytes=1024,
                backup_count=2
            )
            
            # Write enough to trigger rotation
            for i in range(100):
                logger.info("X" * 100)
            
            # Check that backup files exist
            backup_files = list(Path(tmpdir).glob("rotation_test.log.*"))
            assert len(backup_files) <= 2

class TestLogMetric:
    def test_log_metric_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "metric_test.log"
            metrics_file = Path(tmpdir) / "metrics.jsonl"
            
            logger = get_logger(
                "test_log_metric",
                log_file=str(log_file),
                metrics_file=str(metrics_file)
            )
            
            log_metric(logger, "test_metric", 42.5, context="test")
            
            assert metrics_file.exists()
            with open(metrics_file, "r") as f:
                content = f.read()
                assert "test_metric" in content
                assert "42.5" in content

class TestSetupDefaultLoggers:
    def test_setup_loggers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loggers = setup_default_loggers(project_root=tmpdir)
            
            assert "root" in loggers
            assert "generation" in loggers
            assert "filtering" in loggers
            assert "training" in loggers
            
            for name, logger in loggers.items():
                assert logger is not None
                assert logger.name.startswith("llmXive")

class TestGetDefaultLogger:
    def test_default_logger_singleton(self):
        logger1 = get_default_logger()
        logger2 = get_default_logger()
        
        assert logger1 is logger2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])