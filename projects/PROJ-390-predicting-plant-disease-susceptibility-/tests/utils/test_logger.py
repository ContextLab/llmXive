import pytest
import logging
import os
import json
from pathlib import Path
import sys
import time
import tempfile
import shutil

# Import the module under test
# Ensure the path is correct relative to the test runner
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.logger import (
    JSONFormatter,
    PlainTextFormatter,
    get_logger,
    log_error,
    log_warning,
    log_info,
    log_debug,
    setup_logging_for_task,
    close_logging
)

class TestLoggerInitialization:
    def test_get_logger_creates_logger(self):
        logger = get_logger("test_init")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_init"
        assert len(logger.handlers) > 0
        close_logging()

    def test_get_logger_idempotent(self):
        name = "test_idempotent"
        logger1 = get_logger(name)
        initial_count = len(logger1.handlers)
        logger2 = get_logger(name)
        # Should not add duplicate handlers
        assert len(logger2.handlers) == initial_count
        close_logging()

class TestLoggingFunctions:
    def test_log_info(self, caplog):
        logger = get_logger("test_info", level=logging.DEBUG)
        # Caplog captures the output if we attach it, but here we test the function logic
        # We will verify side effects by checking if the handler receives the record
        with caplog.at_level(logging.INFO):
            log_info(logger, "Test info message")
            assert "Test info message" in caplog.text
        close_logging()

    def test_log_warning(self, caplog):
        logger = get_logger("test_warn", level=logging.WARNING)
        with caplog.at_level(logging.WARNING):
            log_warning(logger, "Test warning message")
            assert "Test warning message" in caplog.text
        close_logging()

    def test_log_error(self, caplog):
        logger = get_logger("test_err", level=logging.ERROR)
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error")
            except Exception as e:
                log_error(logger, "An error occurred", exc=e)
                assert "An error occurred" in caplog.text
        close_logging()

    def test_log_debug(self, caplog):
        logger = get_logger("test_dbg", level=logging.DEBUG)
        with caplog.at_level(logging.DEBUG):
            log_debug(logger, "Test debug message")
            assert "Test debug message" in caplog.text
        close_logging()

class TestJSONFormatter:
    def test_format_produces_valid_json(self):
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
        parsed = json.loads(output)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert parsed["logger"] == "test"

    def test_format_includes_exception(self):
        formatter = JSONFormatter()
        try:
            raise RuntimeError("Boom")
        except Exception:
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
            assert parsed["exception"]["type"] == "RuntimeError"

    def test_format_includes_extra_data(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test with data",
            args=(),
            exc_info=None
        )
        record.extra_data = {"key": "value", "num": 123}
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["num"] == 123

class TestPlainTextFormatter:
    def test_format_produces_text(self):
        formatter = PlainTextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Plain text message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        assert isinstance(output, str)
        assert "Plain text message" in output
        assert "INFO" in output

class TestSetupLoggingForTask:
    def test_creates_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            logger = setup_logging_for_task("test_task", base_log_dir=log_dir)
            
            # Check file exists
            log_file = log_dir / "test_task.log"
            assert log_file.exists()
            
            # Log something
            log_info(logger, "Task started")
            
            # Verify content
            content = log_file.read_text()
            assert "Task started" in content
            # Verify it is JSON
            json.loads(content.strip())
            
            close_logging()

class TestCloseLogging:
    def test_closes_handlers(self):
        logger = get_logger("test_close")
        initial_handlers = len(logger.handlers)
        assert initial_handlers > 0
        
        close_logging()
        
        # After close, handlers should be removed
        assert len(logger.handlers) == 0

# Cleanup fixture to ensure tests don't leave handlers behind
@pytest.fixture(autouse=True)
def cleanup_logging_fixture():
    yield
    close_logging()