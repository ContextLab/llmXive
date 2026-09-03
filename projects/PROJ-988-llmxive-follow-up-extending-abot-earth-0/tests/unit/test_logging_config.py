"""
Unit tests for the logging configuration module.
"""
import os
import sys
import json
import tempfile
import logging
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from lib.logging_config import setup_logging, get_logger, log_structured_message, JsonFormatter

class TestJsonFormatter:
    def test_format_returns_json_string(self):
        """Verify that the formatter returns a valid JSON string."""
        formatter = JsonFormatter()
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
        assert isinstance(output, str)
        # Verify it is valid JSON
        parsed = json.loads(output)
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"

    def test_format_includes_exception(self):
        """Verify exception info is included when present."""
        formatter = JsonFormatter()
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
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_format_includes_extra_data(self):
        """Verify extra data is merged into the JSON output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.extra_data = {"user_id": 123, "action": "login"}
        
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["user_id"] == 123
        assert parsed["action"] == "login"

class TestSetupLogging:
    def test_creates_log_file(self, tmp_path):
        """Verify that setup_logging creates the log file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, console_output=False)
        
        # The file should exist after the first log write, but setup_logging
        # itself doesn't write. We force a write to ensure file creation.
        logger = get_logger("test_setup")
        logger.info("Initialization check")
        
        assert log_file.exists()

    def test_logs_to_file(self, tmp_path):
        """Verify that logs are written to the specified file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, console_output=False)
        
        logger = get_logger("test_file_write")
        logger.info("Message to file")
        
        content = log_file.read_text()
        assert "Message to file" in content
        # Verify JSON structure
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip():
                json.loads(line)

    def test_console_output_enabled(self, capsys):
        """Verify that console output is enabled when requested."""
        setup_logging(console_output=True)
        logger = get_logger("test_console")
        logger.info("Console message")
        
        captured = capsys.readouterr()
        assert "Console message" in captured.out

class TestLogStructuredMessage:
    def test_includes_extra_fields(self, tmp_path):
        """Verify that structured messages include extra fields."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, console_output=False)
        
        logger = get_logger("test_struct")
        log_structured_message(logger, logging.INFO, "Structured log", user="alice", score=99)
        
        content = log_file.read_text()
        parsed = json.loads(content.strip())
        assert parsed["user"] == "alice"
        assert parsed["score"] == 99