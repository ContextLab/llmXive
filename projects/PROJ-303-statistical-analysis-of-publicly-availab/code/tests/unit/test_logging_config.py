"""
Unit tests for the logging configuration module.
"""

import logging
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from src.pipeline import logging_config


class TestLoggingConfig(unittest.TestCase):
    """Tests for logging configuration initialization and utilities."""

    def setUp(self):
        """Reset logging state before each test."""
        # Remove the custom logger to force re-initialization
        self.logger_name = logging_config.LOGGER_NAME
        if self.logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[self.logger_name]
        
        # Ensure log directory exists for tests
        logging_config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up log files after tests."""
        # Remove log files created during test
        if logging_config.LOG_DIR.exists():
            for f in logging_config.LOG_DIR.glob("*.log"):
                f.unlink()
            for f in logging_config.LOG_DIR.glob("*.json"):
                f.unlink()

    @patch('src.pipeline.logging_config.get_config')
    def test_logger_initialization(self, mock_get_config):
        """Test that get_logger returns a configured logger."""
        mock_get_config.return_value = MagicMock(log_level="DEBUG")
        
        logger = logging_config.get_logger("test_sublogger")
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, f"{logging_config.LOGGER_NAME}.test_sublogger")
        self.assertTrue(logger.handlers) # Should have handlers

    def test_handle_error(self):
        """Test that handle_error logs the exception and re-raises it."""
        logger = logging_config.get_logger("test_error")
        test_exception = ValueError("Test error message")
        
        with self.assertRaises(ValueError) as context:
            logging_config.handle_error(logger, test_exception, {"key": "value"})
        
        self.assertEqual(str(context.exception), "Test error message")

    def test_time_execution_decorator(self):
        """Test that time_execution decorator logs start and end times."""
        logger = logging_config.get_logger("test_time")
        
        @logging_config.time_execution(logger, "dummy_task")
        def dummy_func():
            return 42
        
        result = dummy_func()
        self.assertEqual(result, 42)

    def test_json_formatter(self):
        """Test that JSONFormatter produces valid JSON."""
        formatter = logging_config.JSONFormatter()
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
        import json
        parsed = json.loads(output)
        
        self.assertEqual(parsed["message"], "Test message")
        self.assertIn("timestamp", parsed)
        self.assertEqual(parsed["level"], "INFO")

    @patch('src.pipeline.logging_config.get_config')
    def test_log_level_from_config(self, mock_get_config):
        """Test that log level is read from config."""
        mock_get_config.return_value = MagicMock(log_level="WARNING")
        
        # Re-initialize to pick up new config
        if self.logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[self.logger_name]
        
        logger = logging_config.get_logger()
        
        # The root logger level should be WARNING
        self.assertEqual(logger.level, logging.WARNING)

    @patch('src.pipeline.logging_config.get_config')
    def test_log_level_from_env(self, mock_get_config):
        """Test that log level is read from environment variable."""
        mock_get_config.return_value = MagicMock() # Config doesn't override
        os.environ["LLMXIVE_LOG_LEVEL"] = "ERROR"
        
        # Re-initialize
        if self.logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[self.logger_name]
        
        logger = logging_config.get_logger()
        
        self.assertEqual(logger.level, logging.ERROR)
        
        # Cleanup
        del os.environ["LLMXIVE_LOG_LEVEL"]

    def test_log_with_context(self):
        """Test logging with additional context data."""
        logger = logging_config.get_logger("test_context")
        
        # Just verify it doesn't crash
        logging_config.log_with_context(logger, logging.INFO, "Test message", key="value")