"""
Unit tests for the structured logging module (T008).

Verifies JSON output format, file creation, and logging functionality.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from src.utils.logging import (
    PipelineLogger,
    get_logger,
    log_event,
    log_error,
    log_progress,
    JsonFormatter
)
from src.utils.config import get_config, set_config


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""

    def test_format_returns_valid_json(self):
        """Test that format returns a valid JSON string."""
        formatter = JsonFormatter()
        
        # Create a mock log record
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
        parsed = json.loads(output)
        
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"
        assert parsed["function"] == ""
        assert parsed["line"] == 10

    def test_format_includes_exception_info(self):
        """Test that exception info is included when present."""
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
                lineno=20,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            output = formatter.format(record)
            parsed = json.loads(output)
            
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]

    def test_format_includes_extra_fields(self):
        """Test that extra fields are included in output."""
        formatter = JsonFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"custom_key": "custom_value", "count": 42}
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["custom_key"] == "custom_value"
        assert parsed["count"] == 42


class TestPipelineLogger:
    """Tests for the PipelineLogger singleton."""

    def test_singleton_instance(self):
        """Test that PipelineLogger returns the same instance."""
        logger1 = PipelineLogger()
        logger2 = PipelineLogger()
        
        assert logger1 is logger2

    def test_logger_configuration(self, tmp_path):
        """Test that logger is configured with JSON output to file."""
        # Setup config with temporary directory
        config = get_config()
        original_logs_path = config["paths"]["logs"]
        
        # Use temp directory for test
        test_logs_dir = tmp_path / "logs"
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporarily override config
        config["paths"]["logs"] = str(test_logs_dir)
        
        try:
            # Force re-initialization by creating a new instance
            PipelineLogger._instance = None
            logger_instance = PipelineLogger()
            logger_instance._initialized = False
            logger_instance._setup()
            
            # Verify handlers were added
            assert len(logger_instance.get_logger().handlers) >= 1
            
            # Verify file handler exists
            file_handler = None
            for handler in logger_instance.get_logger().handlers:
                if isinstance(handler, logging.FileHandler):
                    file_handler = handler
                    break
            
            assert file_handler is not None
            
            # Check that log file exists after logging
            logger_instance.log_event("test_event", test_key="test_value")
            
            log_file = test_logs_dir / "pipeline.jsonl"
            assert log_file.exists()
            
            # Verify JSON format
            with open(log_file, 'r') as f:
                line = f.readline()
                parsed = json.loads(line)
                
            assert parsed["event"] == "test_event"
            assert parsed["test_key"] == "test_value"
            
        finally:
            # Restore original config
            config["paths"]["logs"] = original_logs_path
            PipelineLogger._instance = None

    def test_log_event(self, tmp_path):
        """Test the log_event method."""
        config = get_config()
        original_logs_path = config["paths"]["logs"]
        
        test_logs_dir = tmp_path / "logs"
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        config["paths"]["logs"] = str(test_logs_dir)
        
        try:
            PipelineLogger._instance = None
            logger_instance = PipelineLogger()
            logger_instance._initialized = False
            logger_instance._setup()
            
            logger_instance.log_event("data_loaded", file="test.csv", rows=1000)
            
            log_file = test_logs_dir / "pipeline.jsonl"
            with open(log_file, 'r') as f:
                line = f.readline()
                parsed = json.loads(line)
            
            assert parsed["event"] == "data_loaded"
            assert parsed["file"] == "test.csv"
            assert parsed["rows"] == 1000
            
        finally:
            config["paths"]["logs"] = original_logs_path
            PipelineLogger._instance = None

    def test_log_error(self, tmp_path):
        """Test the log_error method."""
        config = get_config()
        original_logs_path = config["paths"]["logs"]
        
        test_logs_dir = tmp_path / "logs"
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        config["paths"]["logs"] = str(test_logs_dir)
        
        try:
            PipelineLogger._instance = None
            logger_instance = PipelineLogger()
            logger_instance._initialized = False
            logger_instance._setup()
            
            logger_instance.log_error("Something went wrong", error_code=500, stage="preprocess")
            
            log_file = test_logs_dir / "pipeline.jsonl"
            with open(log_file, 'r') as f:
                line = f.readline()
                parsed = json.loads(line)
            
            assert parsed["level"] == "ERROR"
            assert "Something went wrong" in parsed["message"]
            assert parsed["error_code"] == 500
            assert parsed["stage"] == "preprocess"
            
        finally:
            config["paths"]["logs"] = original_logs_path
            PipelineLogger._instance = None

    def test_log_progress(self, tmp_path):
        """Test the log_progress method."""
        config = get_config()
        original_logs_path = config["paths"]["logs"]
        
        test_logs_dir = tmp_path / "logs"
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        config["paths"]["logs"] = str(test_logs_dir)
        
        try:
            PipelineLogger._instance = None
            logger_instance = PipelineLogger()
            logger_instance._initialized = False
            logger_instance._setup()
            
            logger_instance.log_progress("preprocessing", 50, 100)
            
            log_file = test_logs_dir / "pipeline.jsonl"
            with open(log_file, 'r') as f:
                line = f.readline()
                parsed = json.loads(line)
            
            assert parsed["event"] == "progress"
            assert parsed["stage"] == "preprocessing"
            assert parsed["progress"] == 50
            assert parsed["total"] == 100
            assert parsed["percent"] == 50.0
            
        finally:
            config["paths"]["logs"] = original_logs_path
            PipelineLogger._instance = None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_logger_returns_valid_logger(self, tmp_path):
        """Test that get_logger returns a configured logger."""
        config = get_config()
        original_logs_path = config["paths"]["logs"]
        
        test_logs_dir = tmp_path / "logs"
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        config["paths"]["logs"] = str(test_logs_dir)
        
        try:
            PipelineLogger._instance = None
            logger = get_logger()
            
            assert isinstance(logger, logging.Logger)
            assert logger.name == "pipeline"
            
        finally:
            config["paths"]["logs"] = original_logs_path
            PipelineLogger._instance = None

    def test_log_event_function(self, tmp_path):
        """Test the log_event convenience function."""
        config = get_config()
        original_logs_path = config["paths"]["logs"]
        
        test_logs_dir = tmp_path / "logs"
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        config["paths"]["logs"] = str(test_logs_dir)
        
        try:
            PipelineLogger._instance = None
            log_event("test_convenience", value=123)
            
            log_file = test_logs_dir / "pipeline.jsonl"
            assert log_file.exists()
            
            with open(log_file, 'r') as f:
                line = f.readline()
                parsed = json.loads(line)
            
            assert parsed["event"] == "test_convenience"
            assert parsed["value"] == 123
            
        finally:
            config["paths"]["logs"] = original_logs_path
            PipelineLogger._instance = None


import logging
pytest_plugins = []
