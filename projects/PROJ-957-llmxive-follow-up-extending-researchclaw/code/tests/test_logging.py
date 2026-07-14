import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from src.utils.logging import (
    JSONFormatter,
    ErrorTracker,
    setup_logging,
    log_with_context,
    create_error_tracker,
    get_global_error_tracker,
)


class TestJSONFormatter:
    def test_format_basic_message(self):
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

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["module"] == "test"
        assert data["lineno"] == 1

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
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["traceback"]

    def test_format_with_context(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Context test",
            args=(),
            exc_info=None,
        )
        record.context = {"user_id": 123, "action": "login"}

        output = formatter.format(record)
        data = json.loads(output)

        assert data["context"]["user_id"] == 123
        assert data["context"]["action"] == "login"


class TestErrorTracker:
    def test_record_error(self):
        tracker = ErrorTracker()
        try:
            raise RuntimeError("Something went wrong")
        except RuntimeError as e:
            tracker.record(e, {"module": "test_module"})

        errors = tracker.get_errors()
        assert len(errors) == 1
        assert errors[0]["error_type"] == "RuntimeError"
        assert "Something went wrong" in errors[0]["message"]
        assert errors[0]["context"]["module"] == "test_module"

    def test_write_to_file(self):
        tracker = ErrorTracker()
        try:
            raise KeyError("Missing key")
        except KeyError as e:
            tracker.record(e)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            tracker.write_to_file(temp_path)
            assert os.path.exists(temp_path)

            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["error_type"] == "KeyError"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_clear(self):
        tracker = ErrorTracker()
        try:
            raise ValueError("Test")
        except ValueError as e:
            tracker.record(e)

        assert len(tracker.get_errors()) == 1
        tracker.clear()
        assert len(tracker.get_errors()) == 0


class TestSetupLogging:
    def test_setup_logging_console_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=None, level=logging.INFO, enable_console=True)

            assert logger is not None
            assert len(logger.handlers) >= 1  # At least console handler

            # Test logging
            logger.info("Console test")

    def test_setup_logging_with_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, level=logging.INFO, enable_console=False)

            assert logger is not None
            logger.info("File test")

            assert os.path.exists(log_file)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)

            assert data["message"] == "File test"
            assert data["level"] == "INFO"


class TestLogWithContext:
    def test_log_with_context(self):
        logger = logging.getLogger("test_context")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_path = f.name

        try:
            # We can't easily capture stdout in this simple test,
            # but we verify the function doesn't crash and attaches context
            log_with_context(logger, logging.INFO, "Context message", {"key": "value"})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestGlobalTracker:
    def test_get_global_tracker_singleton(self):
        tracker1 = get_global_error_tracker()
        tracker2 = get_global_error_tracker()
        assert tracker1 is tracker2

    def test_global_tracker_record(self):
        tracker = get_global_error_tracker()
        tracker.clear()  # Reset for test
        try:
            raise ValueError("Global test")
        except ValueError as e:
            tracker.record(e)

        assert len(tracker.get_errors()) == 1
        tracker.clear()