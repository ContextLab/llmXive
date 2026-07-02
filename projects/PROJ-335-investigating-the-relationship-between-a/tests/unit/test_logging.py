"""
Unit tests for the logging configuration module.
"""
import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import io

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from utils.logging_config import (
    setup_logging,
    get_logger,
    log_metric,
    StructuredFormatter
)


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""
    
    def test_format_creates_json(self):
        """Verify that format returns a valid JSON string."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "level" in parsed
        assert "message" in parsed
        assert parsed["message"] == "Test message"
    
    def test_format_includes_timestamp(self):
        """Verify that timestamp is included by default."""
        formatter = StructuredFormatter(include_timestamp=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "timestamp" in parsed
    
    def test_format_excludes_timestamp(self):
        """Verify that timestamp can be excluded."""
        formatter = StructuredFormatter(include_timestamp=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "timestamp" not in parsed
    
    def test_format_includes_exception(self):
        """Verify that exceptions are included in log output."""
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
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            result = formatter.format(record)
            parsed = json.loads(result)
            
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]


class TestSetupLogging:
    """Tests for the setup_logging function."""
    
    def test_creates_log_directory(self, tmp_path):
        """Verify that log directory is created if it doesn't exist."""
        log_dir = tmp_path / "custom_logs"
        
        logger = setup_logging(log_dir=str(log_dir))
        
        assert log_dir.exists()
    
    def test_returns_logger(self, tmp_path):
        """Verify that a logger instance is returned."""
        log_dir = tmp_path / "logs"
        
        logger = setup_logging(log_dir=str(log_dir))
        
        assert isinstance(logger, logging.Logger)
    
    def test_console_handler_exists(self, tmp_path):
        """Verify that console handler is added."""
        log_dir = tmp_path / "logs"
        
        logger = setup_logging(log_dir=str(log_dir))
        
        console_handlers = [
            h for h in logger.handlers 
            if isinstance(h, logging.StreamHandler)
        ]
        
        assert len(console_handlers) > 0
    
    def test_file_handler_exists(self, tmp_path):
        """Verify that file handler is added."""
        log_dir = tmp_path / "logs"
        
        logger = setup_logging(log_dir=str(log_dir))
        
        file_handlers = [
            h for h in logger.handlers 
            if isinstance(h, logging.FileHandler)
        ]
        
        assert len(file_handlers) > 0
    
    def test_file_handler_uses_structured_formatter(self, tmp_path):
        """Verify that file handler uses StructuredFormatter."""
        log_dir = tmp_path / "logs"
        
        logger = setup_logging(log_dir=str(log_dir))
        
        file_handlers = [
            h for h in logger.handlers 
            if isinstance(h, logging.FileHandler)
        ]
        
        assert len(file_handlers) > 0
        assert isinstance(file_handlers[0].formatter, StructuredFormatter)
    
    def test_log_levels_configured(self, tmp_path):
        """Verify that log levels are configured correctly."""
        log_dir = tmp_path / "logs"
        
        logger = setup_logging(
            log_dir=str(log_dir),
            console_level="WARNING",
            file_level="DEBUG"
        )
        
        console_handlers = [
            h for h in logger.handlers 
            if isinstance(h, logging.StreamHandler)
        ]
        file_handlers = [
            h for h in logger.handlers 
            if isinstance(h, logging.FileHandler)
        ]
        
        assert console_handlers[0].level == logging.WARNING
        assert file_handlers[0].level == logging.DEBUG


class TestGetLogger:
    """Tests for the get_logger function."""
    
    def test_returns_named_logger(self):
        """Verify that a named logger is returned."""
        logger = get_logger("test_module")
        
        assert logger.name == "test_module"
    
    def test_returns_different_instances(self):
        """Verify that different names return different logger instances."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"


class TestLogMetric:
    """Tests for the log_metric function."""
    
    def test_logs_metric_with_context(self, tmp_path):
        """Verify that metrics are logged with context."""
        log_dir = tmp_path / "logs"
        logger = setup_logging(log_dir=str(log_dir))
        
        # Capture log output
        with patch.object(logger, 'handle') as mock_handle:
            log_metric(
                logger,
                "alpha_power",
                0.85,
                subject_id="sub-001",
                trial_id="trial-01"
            )
            
            assert mock_handle.called
            record = mock_handle.call_args[0][0]
            assert hasattr(record, 'extra_data')
            assert record.extra_data["metric_name"] == "alpha_power"
            assert record.extra_data["metric_value"] == 0.85
            assert record.extra_data["subject_id"] == "sub-001"
            assert record.extra_data["trial_id"] == "trial-01"
    
    def test_logs_metric_without_optional_fields(self, tmp_path):
        """Verify that metrics can be logged without optional fields."""
        log_dir = tmp_path / "logs"
        logger = setup_logging(log_dir=str(log_dir))
        
        with patch.object(logger, 'handle') as mock_handle:
            log_metric(logger, "plv_value", 0.42)
            
            assert mock_handle.called
            record = mock_handle.call_args[0][0]
            assert hasattr(record, 'extra_data')
            assert record.extra_data["metric_name"] == "plv_value"
            assert record.extra_data["metric_value"] == 0.42
            assert "subject_id" not in record.extra_data
            assert "trial_id" not in record.extra_data
    
    def test_logs_extra_kwargs(self, tmp_path):
        """Verify that extra keyword arguments are included."""
        log_dir = tmp_path / "logs"
        logger = setup_logging(log_dir=str(log_dir))
        
        with patch.object(logger, 'handle') as mock_handle:
            log_metric(
                logger,
                "metric",
                1.0,
                electrode="Fz",
                condition="n_back"
            )
            
            record = mock_handle.call_args[0][0]
            assert record.extra_data["electrode"] == "Fz"
            assert record.extra_data["condition"] == "n_back"