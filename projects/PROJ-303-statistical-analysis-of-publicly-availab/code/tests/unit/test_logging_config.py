import logging
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import json

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.pipeline.logging_config import (
    JSONFormatter, 
    get_logger, 
    handle_error, 
    log_with_context, 
    time_execution
)

class TestLoggingConfig(unittest.TestCase):
    
    def setUp(self):
        """Setup temporary log directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = "state/logs"
        # Patch the LOG_DIR logic by temporarily modifying the module if needed,
        # but primarily we test the formatter and logger creation logic.
        # For this test, we assume the module uses the global LOG_DIR which we can't easily override
        # without reloading, so we focus on the JSONFormatter and basic logger behavior.
        
    def test_json_formatter_basic(self):
        """Test that JSONFormatter produces valid JSON with required fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message %s",
            args=("arg1",),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["message"], "Test message arg1")
        self.assertIn("timestamp", parsed)
        self.assertIn("logger", parsed)
        self.assertIn("module", parsed)

    def test_json_formatter_with_exception(self):
        """Test that JSONFormatter includes exception traceback."""
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
                lineno=20,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            formatted = formatter.format(record)
            parsed = json.loads(formatted)
            
            self.assertIn("exception", parsed)
            self.assertEqual(parsed["exception"]["type"], "ValueError")
            self.assertIn("traceback", parsed["exception"])

    def test_get_logger_creates_handlers(self):
        """Test that get_logger creates handlers and does not duplicate them on second call."""
        logger_name = "test_unique_logger"
        
        # Clear any existing handlers for this name if the module is cached
        # In a real run, the registry check prevents this, but here we rely on the module logic
        logger1 = get_logger(logger_name)
        num_handlers = len(logger1.handlers)
        
        # Call again
        logger2 = get_logger(logger_name)
        
        self.assertEqual(logger1, logger2)
        self.assertEqual(len(logger2.handlers), num_handlers) # Should not increase
        self.assertTrue(num_handlers > 0)

    def test_log_with_context(self):
        """Test logging with extra context data."""
        with patch('src.pipeline.logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            log_with_context("test_mod", "Hello", level=logging.WARNING, context={"key": "value"})
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            # Check that extra context was passed
            self.assertIn("extra", call_args.kwargs)
            self.assertEqual(call_args.kwargs["extra"]["context"]["key"], "value")

    def test_time_execution_decorator_success(self):
        """Test time_execution decorator on a successful function."""
        @time_execution
        def dummy_func():
            return "done"
        
        with patch('src.pipeline.logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = dummy_func()
            self.assertEqual(result, "done")
            
            # Check for start and end logs
            calls = mock_logger.info.call_args_list
            self.assertGreaterEqual(len(calls), 2)
            
            # Verify one call mentions "Starting" and one mentions "Completed"
            messages = [str(c) for c in calls]
            self.assertTrue(any("Starting" in m for m in messages))
            self.assertTrue(any("Completed" in m for m in messages))

    def test_time_execution_decorator_failure(self):
        """Test time_execution decorator on a failing function."""
        @time_execution
        def failing_func():
            raise RuntimeError("Oops")
        
        with patch('src.pipeline.logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            with self.assertRaises(RuntimeError):
                failing_func()
            
            # Check for error log
            mock_logger.error.assert_called()
            # Verify context contains failure status
            call_kwargs = mock_logger.error.call_args.kwargs
            self.assertIn("extra", call_kwargs)
            self.assertEqual(call_kwargs["extra"]["context"]["status"], "failed")

    def test_handle_error_logs_and_raises(self):
        """Test that handle_error logs the error and re-raises it."""
        test_error = ValueError("Test handle error")
        
        with patch('src.pipeline.logging_config.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            with self.assertRaises(ValueError):
                handle_error(test_error, context={"step": "validation"})
            
            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args.kwargs
            self.assertIn("extra", call_kwargs)
            self.assertEqual(call_kwargs["extra"]["context"]["error_type"], "ValueError")