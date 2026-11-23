"""
Unit tests for the structured logging module.
"""

import pytest
import logging
import json
import sys
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.logging import (
    setup_logging,
    get_logger,
    log_step_start,
    log_step_complete,
    log_step_error,
    log_metric,
    log_event_processed,
    StructuredFormatter,
    PIPELINE_LOGGER_NAME,
)


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""

    def test_format_produces_valid_json(self):
        """Test that the formatter outputs valid JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"
        assert parsed["line"] == 10

    def test_format_includes_extra_context(self):
        """Test that extra context is included in JSON output."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.step = "download"
        record.event_id = "GW150914"
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["step"] == "download"
        assert parsed["event_id"] == "GW150914"

    def test_format_includes_exception_info(self):
        """Test that exception info is included when present."""
        formatter = StructuredFormatter()
        
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
            parsed = json.loads(output)
            
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a logger instance."""
        logger = setup_logging(log_level=logging.DEBUG)
        assert isinstance(logger, logging.Logger)
        assert logger.name == PIPELINE_LOGGER_NAME

    def test_setup_logging_sets_level(self):
        """Test that setup_logging sets the correct log level."""
        logger = setup_logging(log_level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_setup_logging_console_handler(self):
        """Test that console handler is added."""
        logger = setup_logging()
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logging_file_handler(self, tmp_path):
        """Test that file handler is added when log_file is provided."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file)
        
        assert len(logger.handlers) >= 2
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_setup_logging_json_format(self):
        """Test that JSON formatter is used by default."""
        logger = setup_logging()
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                assert isinstance(handler.formatter, StructuredFormatter)
                break

    def test_setup_logging_human_readable_format(self, tmp_path):
        """Test that human-readable formatter is used when json_format=False."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, json_format=False)
        
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                assert not isinstance(handler.formatter, StructuredFormatter)
                break

    def test_setup_logging_idempotent(self):
        """Test that setup_logging returns the same logger on subsequent calls."""
        logger1 = setup_logging(log_level=logging.DEBUG)
        logger2 = setup_logging(log_level=logging.WARNING)
        assert logger1 is logger2


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        # Ensure logging is set up
        setup_logging()
        logger = get_logger()
        assert isinstance(logger, logging.Logger)

    def test_get_logger_raises_if_not_setup(self):
        """Test that get_logger auto-initializes if not explicitly set."""
        # Reset the global logger
        import src.utils.logging as logging_module
        logging_module._logger = None
        
        # Should not raise, should auto-initialize
        logger = get_logger()
        assert isinstance(logger, logging.Logger)


class TestLoggingHelpers:
    """Tests for helper logging functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset global logger state
        import src.utils.logging as logging_module
        logging_module._logger = None
        logging_module._handler = None
        
        # Set up logging with a StringIO handler for capture
        self.log_stream = io.StringIO()
        self.logger = setup_logging(log_level=logging.DEBUG)
        
        # Remove default handlers and add our capture handler
        self.logger.handlers.clear()
        capture_handler = logging.StreamHandler(self.log_stream)
        capture_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(capture_handler)

    def test_log_step_start(self):
        """Test logging step start."""
        log_step_start("download", event_id="GW150914")
        output = self.log_stream.getvalue()
        parsed = json.loads(output)
        
        assert parsed["step"] == "download"
        assert "started" in parsed["message"]
        assert parsed["event_id"] == "GW150914"

    def test_log_step_complete(self):
        """Test logging step completion."""
        log_step_complete("inject", files_processed=10)
        output = self.log_stream.getvalue()
        parsed = json.loads(output)
        
        assert parsed["step"] == "inject"
        assert "completed" in parsed["message"]
        assert parsed["files_processed"] == 10

    def test_log_step_error(self):
        """Test logging step error."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            log_step_error("validate", error=e, event_id="GW150914")
        
        output = self.log_stream.getvalue()
        parsed = json.loads(output)
        
        assert parsed["step"] == "validate"
        assert "failed" in parsed["message"]
        assert "ValueError" in parsed["exception"]

    def test_log_metric(self):
        """Test logging a metric."""
        log_metric("snr", 25.5, step="compress", event_id="GW150914")
        output = self.log_stream.getvalue()
        parsed = json.loads(output)
        
        assert parsed["metric_name"] == "snr"
        assert parsed["metric_value"] == 25.5
        assert parsed["step"] == "compress"

    def test_log_event_processed(self):
        """Test logging event processing status."""
        log_event_processed("GW150914", "success", snr=25.5)
        output = self.log_stream.getvalue()
        parsed = json.loads(output)
        
        assert parsed["event_id"] == "GW150914"
        assert parsed["status"] == "success"
        assert parsed["snr"] == 25.5