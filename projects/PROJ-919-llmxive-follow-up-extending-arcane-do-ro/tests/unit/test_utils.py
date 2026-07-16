"""
Unit tests for the logging infrastructure in src/lib/utils.py.
"""
import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
from src.lib.utils import (
    JSONFormatter,
    get_logger,
    init_project_logger,
    get_project_logger,
    log_event,
)


class TestJSONFormatter:
    def test_format_basic(self):
        """Test that basic log records are formatted as valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message %s",
            args=("arg1",),
            exc_info=None,
        )

        output = formatter.format(record)
        assert isinstance(output, str)
        
        # Parse JSON to ensure it's valid
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message arg1"
        assert parsed["module"] == "test"
        assert parsed["function"] is None
        assert "timestamp" in parsed

    def test_format_with_exception(self):
        """Test that exceptions are captured in the JSON output."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            import traceback
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestGetLogger:
    def test_console_handler_only(self, capsys):
        """Test logger with only console handler."""
        logger = get_logger("test_console", log_file=None, enable_console=True)
        logger.info("Console only")

        captured = capsys.readouterr()
        assert "Console only" in captured.out
        parsed = json.loads(captured.out.strip())
        assert parsed["level"] == "INFO"

    def test_file_handler_creation(self, tmp_path):
        """Test that file handler creates the log file and writes JSON."""
        log_file = tmp_path / "test.log"
        logger = get_logger("test_file", log_file=str(log_file), enable_console=False)
        
        logger.info("File only message")

        assert log_file.exists()
        content = log_file.read_text().strip()
        parsed = json.loads(content)
        assert parsed["message"] == "File only message"
        assert parsed["logger"] == "test_file"

    def test_no_duplicate_handlers(self):
        """Test that calling get_logger twice doesn't duplicate handlers."""
        logger = get_logger("test_dup", log_file=None, enable_console=True)
        initial_count = len(logger.handlers)

        logger2 = get_logger("test_dup", log_file=None, enable_console=True)
        assert logger is logger2
        assert len(logger2.handlers) == initial_count


class TestLogEvent:
    def test_log_event_with_data(self, capsys):
        """Test log_event helper with extra data."""
        logger = get_logger("test_event", log_file=None, enable_console=True)
        
        data = {"user_id": 123, "action": "login"}
        log_event(logger, "User logged in", data=data, level=logging.INFO)

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["message"] == "User logged in"
        assert parsed["data"] == data

class TestProjectLogger:
    def test_init_and_get(self, tmp_path):
        """Test project logger initialization and retrieval."""
        log_dir = tmp_path / "logs"
        init_project_logger(log_dir=str(log_dir), log_filename="proj.log")
        
        logger = get_project_logger()
        assert logger.name == "llmXive"
        assert logger.hasHandlers()

    def test_get_before_init(self):
        """Test that getting logger before init raises error."""
        # Reset global state if necessary (not strictly needed here as test order is managed)
        import src.lib.utils as utils_module
        original = utils_module._project_logger
        utils_module._project_logger = None

        try:
            with pytest.raises(RuntimeError, match="not initialized"):
                get_project_logger()
        finally:
            utils_module._project_logger = original