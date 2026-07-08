"""
Unit tests for the structured logging infrastructure.
"""
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.utils.logging_config import (
    configure_root_logger,
    get_logger,
    StructuredFormatter,
    ContextFilter,
    log_error_with_context,
    log_warning_with_context,
    log_info_with_context,
)


class TestStructuredFormatter:
    """Tests for the JSON log formatter."""

    def test_format_includes_required_fields(self):
        """Verify that formatted logs contain all required fields."""
        formatter = StructuredFormatter(service_name="test-service")
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
        log_entry = json.loads(output)

        assert "timestamp" in log_entry
        assert log_entry["level"] == "INFO"
        assert log_entry["service"] == "test-service"
        assert log_entry["message"] == "Test message"
        assert "context" in log_entry
        assert "correlation_id" in log_entry

    def test_format_includes_exception_info(self):
        """Verify exception info is included when present."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=(ValueError, ValueError("test"), None)
        )
        
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]


class TestContextFilter:
    """Tests for the context injection filter."""

    def test_injects_correlation_id(self):
        """Verify correlation ID is injected if missing."""
        filter_instance = ContextFilter(correlation_id="test-123")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        assert not hasattr(record, "correlation_id")
        result = filter_instance.filter(record)
        
        assert result is True
        assert record.correlation_id == "test-123"

    def test_injects_extra_data(self):
        """Verify extra_data dict is created if missing."""
        filter_instance = ContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, "extra_data")
        assert isinstance(record.extra_data, dict)


class TestGetLogger:
    """Tests for the logger retrieval function."""

    def test_returns_configured_logger(self):
        """Verify get_logger returns a properly configured logger."""
        logger = get_logger("test_module")
        
        assert logger is not None
        assert len(logger.handlers) > 0
        assert logger.name == "test_module"

    def test_caches_logger_instance(self):
        """Verify the same logger instance is returned on subsequent calls."""
        logger1 = get_logger("cached_module")
        logger2 = get_logger("cached_module")
        
        assert logger1 is logger2


class TestLoggingFunctions:
    """Tests for the context-aware logging helpers."""

    def test_log_error_with_context_includes_error_type(self):
        """Verify error logging includes exception type and message."""
        logger = get_logger("test_error")
        test_error = ValueError("Test error message")
        
        with patch.object(logger, 'error') as mock_error:
            log_error_with_context(logger, "Something failed", test_error, {"key": "value"})
            
            # Verify the call was made with correct extra data
            call_args = mock_error.call_args
            assert call_args is not None
            # The extra dict should contain error details
            extra = call_args.kwargs.get('extra', {})
            assert extra.get('extra_data', {}).get('error_type') == "ValueError"
            assert extra.get('extra_data', {}).get('error_message') == "Test error message"

    def test_log_warning_with_context(self):
        """Verify warning logging includes context."""
        logger = get_logger("test_warning")
        
        with patch.object(logger, 'warning') as mock_warning:
            log_warning_with_context(logger, "Warning message", {"warning_code": "W001"})
            
            call_args = mock_warning.call_args
            extra = call_args.kwargs.get('extra', {})
            assert extra.get('extra_data', {}).get('warning_code') == "W001"

    def test_log_info_with_context(self):
        """Verify info logging includes context."""
        logger = get_logger("test_info")
        
        with patch.object(logger, 'info') as mock_info:
            log_info_with_context(logger, "Info message", {"status": "completed"})
            
            call_args = mock_info.call_args
            extra = call_args.kwargs.get('extra', {})
            assert extra.get('extra_data', {}).get('status') == "completed"


class TestConfigureRootLogger:
    """Tests for root logger configuration."""

    def test_configures_handlers(self):
        """Verify root logger has both console and file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the LOG_FILE_DIR to use temp directory
            with patch("code.utils.logging_config.LOG_FILE_DIR", Path(tmpdir)):
                configure_root_logger(level="DEBUG", service_name="test-root")
                
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) == 2
                
                # Check handler types
                handler_types = [type(h).__name__ for h in root_logger.handlers]
                assert "StreamHandler" in handler_types
                assert "FileHandler" in handler_types

    def test_sets_correct_level(self):
        """Verify root logger level is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("code.utils.logging_config.LOG_FILE_DIR", Path(tmpdir)):
                configure_root_logger(level="WARNING", service_name="test-level")
                
                root_logger = logging.getLogger()
                assert root_logger.level == logging.WARNING

    def test_idempotent_configuration(self):
        """Verify calling configure multiple times doesn't add duplicate handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("code.utils.logging_config.LOG_FILE_DIR", Path(tmpdir)):
                configure_root_logger(service_name="test-idem")
                initial_count = len(logging.getLogger().handlers)
                
                configure_root_logger(service_name="test-idem")
                final_count = len(logging.getLogger().handlers)
                
                assert initial_count == final_count
