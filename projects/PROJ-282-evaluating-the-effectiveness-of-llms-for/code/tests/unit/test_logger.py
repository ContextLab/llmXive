"""
Unit tests for the structured logging utility.
"""
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.utils.logger import (
    StructuredFormatter,
    get_logger,
    log_stage_start,
    log_stage_complete,
    log_stage_failure,
    log_artifact,
    create_project_logger,
)


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""

    def test_format_basic_log(self):
        """Test that basic log entries are formatted as JSON."""
        formatter = StructuredFormatter()
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
        parsed = json.loads(output)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert "logger" in parsed

    def test_format_with_stage(self):
        """Test that stage information is included in the log."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.stage = "download"
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["stage"] == "download"

    def test_format_with_exception(self):
        """Test that exceptions are properly formatted."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=sys.exc_info(),
            )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_reuses_existing(self):
        """Test that calling get_logger twice returns the same instance."""
        logger1 = get_logger("test_module_2")
        logger2 = get_logger("test_module_2")
        assert logger1 is logger2

    def test_logger_has_console_handler(self):
        """Test that the logger has a console handler."""
        logger = get_logger("test_module_3")
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0], logging.StreamHandler)


class TestCreateProjectLogger:
    """Tests for the create_project_logger function."""

    def test_create_project_logger_sets_stage(self):
        """Test that the stage is set on the logger."""
        logger = create_project_logger("preprocess")
        assert hasattr(logger, 'stage')
        assert logger.stage == "preprocess"

    def test_create_project_logger_name(self):
        """Test that the logger name includes the stage."""
        logger = create_project_logger("inference")
        assert "llmXive.inference" in logger.name


class TestLoggingFunctions:
    """Tests for the logging helper functions."""

    def test_log_stage_start(self, caplog):
        """Test log_stage_start produces correct output."""
        logger = get_logger("test_start")
        # Clear handlers to avoid duplicate output in tests
        logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        
        with patch.object(logger, 'info') as mock_info:
            log_stage_start(logger, "download")
            mock_info.assert_called_once()
            assert "download" in str(mock_info.call_args)

    def test_log_stage_complete(self, caplog):
        """Test log_stage_complete produces correct output."""
        logger = get_logger("test_complete")
        logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        
        with patch.object(logger, 'info') as mock_info:
            log_stage_complete(logger, "preprocess", duration_ms=1500)
            mock_info.assert_called_once()
            call_args = str(mock_info.call_args)
            assert "preprocess" in call_args
            assert "1500" in call_args

    def test_log_stage_failure(self, caplog):
        """Test log_stage_failure produces correct output."""
        logger = get_logger("test_failure")
        logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        
        with patch.object(logger, 'error') as mock_error:
            log_stage_failure(
                logger, 
                "inference", 
                "Model load failed", 
                error_code="MODEL_LOAD_ERR"
            )
            mock_error.assert_called_once()
            call_args = str(mock_error.call_args)
            assert "inference" in call_args
            assert "MODEL_LOAD_ERR" in call_args

    def test_log_artifact(self, caplog):
        """Test log_artifact produces correct output."""
        logger = get_logger("test_artifact")
        logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        
        with patch.object(logger, 'info') as mock_info:
            log_artifact(
                logger, 
                "data/processed/predictions.csv", 
                "prediction",
                {"rows": 1000}
            )
            mock_info.assert_called_once()
            call_args = str(mock_info.call_args)
            assert "predictions.csv" in call_args
            assert "prediction" in call_args