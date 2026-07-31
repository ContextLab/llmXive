import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.logging_config import (
    JSONFormatter,
    setup_logging,
    get_logger,
    log_event,
)


class TestJSONFormatter:
    def test_format_basic(self):
        """Test that basic log records are formatted as valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert parsed["module"] == "test"
        assert parsed["function"] is None
        assert parsed["line"] == 10

    def test_format_with_exception(self):
        """Test that exceptions are included in the log."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "ERROR"
        assert "exc_info" in parsed
        assert "ValueError" in parsed["exc_info"]

    def test_format_with_extra_data(self):
        """Test that extra data is included in the log."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"event_type": "START", "participant_id": "123"}

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "data" in parsed
        assert parsed["data"]["event_type"] == "START"
        assert parsed["data"]["participant_id"] == "123"


class TestSetupLogging:
    def test_setup_logging_creates_file(self):
        """Test that setup_logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_file, console_output=False)

            assert log_file.exists()

            # Log something to ensure file is written
            logger.info("Test log entry")

            # Verify file is not empty
            assert log_file.stat().st_size > 0

    def test_setup_logging_default_path(self):
        """Test that setup_logging defaults to logs/pipeline.log."""
        # Create a temporary directory to act as project root
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the project root by changing the working directory
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Create a fake module structure
                code_dir = Path(tmpdir) / "code" / "utils"
                code_dir.mkdir(parents=True)
                (code_dir / "__init__.py").touch()

                # Temporarily swap the module path to test default resolution
                import sys
                sys.path.insert(0, tmpdir)
                try:
                    from code.utils.logging_config import setup_logging as local_setup
                    logger = local_setup(console_output=False)
                    # The default path should be relative to the project root (tmpdir)
                    expected_log = Path(tmpdir) / "logs" / "pipeline.log"
                    assert expected_log.exists()
                finally:
                    sys.path.remove(tmpdir)
            finally:
                os.chdir(original_cwd)

    def test_setup_logging_console_output(self):
        """Test that console_output adds a stream handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_file, console_output=True)

            # Check for StreamHandler
            stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(stream_handlers) == 1

    def test_setup_logging_level(self):
        """Test that the logger level is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_file, level=logging.DEBUG, console_output=False)

            assert logger.level == logging.DEBUG


class TestGetLogger:
    def test_get_logger_root(self):
        """Test that get_logger returns the root logger when no name is provided."""
        logger = get_logger()
        assert logger.name == "root"

    def test_get_logger_named(self):
        """Test that get_logger returns a child logger when a name is provided."""
        logger = get_logger("my_module")
        assert logger.name == "my_module"
        assert logger.parent is not None


class TestLogEvent:
    def test_log_event_basic(self):
        """Test that log_event creates a structured log entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_file, console_output=False)

            log_event(logger, "TEST_EVENT", "Test message", {"key": "value"})

            with open(log_file, "r") as f:
                line = f.readline()
                parsed = json.loads(line)

            assert parsed["message"] == "Test message"
            assert parsed["data"]["event_type"] == "TEST_EVENT"
            assert parsed["data"]["key"] == "value"

    def test_log_event_with_level(self):
        """Test that log_event respects the provided level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_file, level=logging.WARNING, console_output=False)

            # This should not be logged because level is INFO < WARNING
            log_event(logger, "TEST_EVENT", "Info message", level=logging.INFO)

            # This should be logged
            log_event(logger, "TEST_EVENT", "Warning message", level=logging.WARNING)

            with open(log_file, "r") as f:
                lines = f.readlines()

            # Should have 2 lines (setup might log something, or just the warning)
            # We specifically check that the warning was logged
            found_warning = False
            for line in lines:
                parsed = json.loads(line)
                if parsed["message"] == "Warning message":
                    found_warning = True
                    break

            assert found_warning
