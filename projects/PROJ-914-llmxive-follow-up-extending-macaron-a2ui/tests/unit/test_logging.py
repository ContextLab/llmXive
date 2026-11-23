"""
Unit tests for the structured JSON logging module.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.utils import logging as log_module


class TestLoggingConfiguration:
    """Tests for logging configuration and initialization."""

    def test_ensure_log_dir_creates_directory(self, tmp_path):
        """Test that log directory is created if it doesn't exist."""
        with patch.object(log_module, 'LOG_DIR', tmp_path / "nonexistent"):
            result = log_module._ensure_log_dir()
            assert result.exists()
            assert result.is_dir()

    def test_get_log_level_default(self):
        """Test default log level when env var is not set."""
        with patch.dict(os.environ, {}, clear=False):
            if log_module.LOG_LEVEL_ENV in os.environ:
                del os.environ[log_module.LOG_LEVEL_ENV]
            assert log_module._get_log_level() == logging.INFO

    def test_get_log_level_from_env(self):
        """Test log level from environment variable."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]
        
        for env_val, expected_level in test_cases:
            with patch.dict(os.environ, {log_module.LOG_LEVEL_ENV: env_val}):
                assert log_module._get_log_level() == expected_level

    def test_get_log_level_invalid_env(self):
        """Test default log level for invalid env value."""
        with patch.dict(os.environ, {log_module.LOG_LEVEL_ENV: "INVALID"}):
            assert log_module._get_log_level() == logging.INFO


class TestJsonFormatter:
    """Tests for JSON log formatting."""

    def test_format_basic_record(self):
        """Test basic log record formatting."""
        formatter = log_module._create_json_formatter()
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
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test"
        assert "filename" in parsed
        assert "line" in parsed

    def test_format_with_extra_data(self):
        """Test formatting with extra data."""
        formatter = log_module._create_json_formatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_data = {"key1": "value1", "key2": 123}
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["key1"] == "value1"
        assert parsed["key2"] == 123

    def test_format_with_state(self):
        """Test formatting includes experiment state when requested."""
        formatter = log_module._create_json_formatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.include_state = True
        
        with patch.object(log_module, 'get_latest_state', return_value={"version": "1.0"}):
            output = formatter.format(record)
            parsed = json.loads(output)
            
            assert "experiment_state" in parsed
            assert parsed["experiment_state"]["version"] == "1.0"


class TestLoggerFunctions:
    """Tests for high-level logging functions."""

    def test_log_experiment_start(self, tmp_path):
        """Test experiment start logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                config = {"param": "value"}
                log_module.log_experiment_start("test_exp", config)
                
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert "test_exp" in call_args[0][0]
                assert call_args[1]["extra"]["extra_data"]["experiment_name"] == "test_exp"

    def test_log_experiment_end(self, tmp_path):
        """Test experiment end logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                metrics = {"accuracy": 0.95}
                log_module.log_experiment_end("test_exp", success=True, metrics=metrics)
                
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert call_args[1]["extra"]["extra_data"]["success"] is True
                assert call_args[1]["extra"]["extra_data"]["metrics"]["accuracy"] == 0.95

    def test_log_metric(self, tmp_path):
        """Test metric logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_module.log_metric("accuracy", 0.95, tags={"split": "test"})
                
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert call_args[1]["extra"]["extra_data"]["metric_name"] == "accuracy"
                assert call_args[1]["extra"]["extra_data"]["metric_value"] == 0.95
                assert call_args[1]["extra"]["extra_data"]["tags"]["split"] == "test"

    def test_log_error(self, tmp_path):
        """Test error logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                test_error = ValueError("Test error")
                log_module.log_error(test_error, context={"step": "validation"})
                
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                assert call_args[1]["extra"]["extra_data"]["error_type"] == "ValueError"
                assert call_args[1]["extra"]["extra_data"]["context"]["step"] == "validation"


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_log_debug(self, tmp_path):
        """Test debug logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_module.log_debug("Debug message", key="value")
                
                mock_logger.debug.assert_called_once()
                assert mock_logger.debug.call_args[1]["extra"]["extra_data"]["key"] == "value"

    def test_log_info(self, tmp_path):
        """Test info logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_module.log_info("Info message")
                
                mock_logger.info.assert_called_once()

    def test_log_warning(self, tmp_path):
        """Test warning logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_module.log_warning("Warning message")
                
                mock_logger.warning.assert_called_once()

    def test_log_error_message(self, tmp_path):
        """Test error message logging."""
        with patch.object(log_module, '_ensure_log_dir', return_value=tmp_path):
            with patch.object(log_module, 'get_experiment_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_module.log_error_message("Error message")
                
                mock_logger.error.assert_called_once()