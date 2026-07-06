"""
Unit tests for the structured logging module (T008).
"""
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import (
    get_logger,
    log_event,
    log_error,
    log_progress,
    JSONFormatter,
)
from src.utils.config import Config


class TestJSONFormatter:
    def test_format_basic_log(self):
        """Test that basic log records are formatted as valid JSON."""
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
        assert "timestamp" in data
        assert data["module"] == "test"

    def test_format_with_exception(self):
        """Test that exceptions are captured in JSON output."""
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
            lineno=20,
            msg="An error occurred",
            args=(),
            exc_info=exc_info
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_extra_fields(self):
        """Test that extra fields attached to records are included."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.task_id = "T008"
        record.subject_id = "sub_001"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["task_id"] == "T008"
        assert data["subject_id"] == "sub_001"


class TestLoggerInitialization:
    def test_get_logger_creates_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger("T001")
        logger2 = get_logger("T002")
        assert logger1 is logger2

    def test_logger_has_handlers(self):
        """Test that the logger has both console and file handlers."""
        logger = get_logger("T003")
        assert len(logger.handlers) >= 2  # Console + File

    def test_log_file_created(self):
        """Test that log files are created in the correct directory."""
        config = Config.get_instance()
        log_dir = Path(config.log_dir)
        assert log_dir.exists()

        # Check if any log file exists
        log_files = list(log_dir.glob("pipeline_*.jsonl"))
        assert len(log_files) > 0


class TestLoggingFunctions:
    def test_log_event_creates_json_entry(self, tmp_path):
        """Test that log_event writes a valid JSON line to the log file."""
        # Temporarily override config log dir
        with patch.object(Config, '_instance') as mock_config:
            mock_config.log_dir = str(tmp_path)
            # Reset singleton to force re-init
            import src.utils.logging as logging_module
            logging_module._logger_instance = None

            logger = get_logger("T008")
            log_event("Test event", level="INFO", task_id="T008", extra_key="extra_value")

            # Find the log file
            log_files = list(tmp_path.glob("pipeline_*.jsonl"))
            assert len(log_files) > 0

            with open(log_files[0], 'r') as f:
                lines = f.readlines()

            assert len(lines) > 0
            data = json.loads(lines[0])
            assert data["message"] == "Test event"
            assert data["task_id"] == "T008"
            assert data["extra_key"] == "extra_value"

    def test_log_error_captures_error_code(self, tmp_path):
        """Test that log_error captures the error_code field."""
        with patch.object(Config, '_instance') as mock_config:
            mock_config.log_dir = str(tmp_path)
            import src.utils.logging as logging_module
            logging_module._logger_instance = None

            log_error("Critical failure", error_code="E001", task_id="T008")

            log_files = list(tmp_path.glob("pipeline_*.jsonl"))
            with open(log_files[0], 'r') as f:
                lines = f.readlines()

            data = json.loads(lines[-1])
            assert data["level"] == "ERROR"
            assert data["error_code"] == "E001"

    def test_log_progress_alias(self, tmp_path):
        """Test that log_progress works as an alias for INFO level."""
        with patch.object(Config, '_instance') as mock_config:
            mock_config.log_dir = str(tmp_path)
            import src.utils.logging as logging_module
            logging_module._logger_instance = None

            log_progress("Progress update", task_id="T008")

            log_files = list(tmp_path.glob("pipeline_*.jsonl"))
            with open(log_files[0], 'r') as f:
                lines = f.readlines()

            data = json.loads(lines[-1])
            assert data["level"] == "INFO"
            assert data["message"] == "Progress update"

    def test_thread_safety(self):
        """Test that logger initialization is thread-safe."""
        import threading
        results = []

        def get_loggers():
            results.append(get_logger("T008"))

        threads = [threading.Thread(target=get_loggers) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should return the same instance
        assert all(r is results[0] for r in results)
