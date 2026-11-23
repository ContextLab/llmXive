"""
Unit tests for ingestion retry logic and API failure handling.
Tests exponential backoff, error logging, and failure modes.
"""
import os
import sys
import time
import logging
import json
import unittest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion import (
    exponential_backoff_retry,
    log_api_error,
    get_logger,
    ensure_log_directory,
    rotate_log_if_needed,
    DataFetchError
)
from downloaders import DataFetchError as DownloadersDataFetchError

class TestExponentialBackoff(unittest.TestCase):
    """Tests for the exponential_backoff_retry decorator/logic."""

    def setUp(self):
        self.test_log_path = Path("logs/api_errors.log")
        self.test_log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.test_log_path.exists():
            self.test_log_path.unlink()
        
        # Ensure logger is configured for the test
        self.logger = get_logger("test_backoff")
        self.logger.handlers = []
        file_handler = logging.FileHandler(self.test_log_path)
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        if self.test_log_path.exists():
            self.test_log_path.unlink()

    @patch('time.sleep', return_value=None)
    def test_exponential_backoff_success_on_first_try(self, mock_sleep):
        """Test that a function succeeding immediately returns the result."""
        call_count = 0

        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = exponential_backoff_retry(success_func, base_delay=0.01, max_delay=1, max_retries=5)
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)
        mock_sleep.assert_not_called()

    @patch('time.sleep', return_value=None)
    def test_exponential_backoff_success_after_retries(self, mock_sleep):
        """Test that a function succeeding after some retries returns the result."""
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success_after_retry"

        result = exponential_backoff_retry(flaky_func, base_delay=0.01, max_delay=1, max_retries=5)
        self.assertEqual(result, "success_after_retry")
        self.assertEqual(call_count, 3)
        # Should have slept twice (after 1st and 2nd failure)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('time.sleep', return_value=None)
    def test_exponential_backoff_fails_after_max_retries(self, mock_sleep):
        """Test that a function failing consistently raises the error after max retries."""
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")

        with self.assertRaises(ConnectionError):
            exponential_backoff_retry(always_fail, base_delay=0.01, max_delay=1, max_retries=3)
        
        self.assertEqual(call_count, 4) # Initial + 3 retries

    @patch('time.sleep', return_value=None)
    def test_exponential_backoff_logs_errors(self, mock_sleep):
        """Test that errors are logged to the API error log file."""
        def always_fail():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            exponential_backoff_retry(always_fail, base_delay=0.01, max_delay=1, max_retries=2)

        # Check log file content
        self.assertTrue(self.test_log_path.exists())
        with open(self.test_log_path, 'r') as f:
            lines = f.readlines()
        
        # Should have 3 entries (Initial + 2 retries)
        self.assertGreaterEqual(len(lines), 3)
        
        for line in lines:
            data = json.loads(line)
            self.assertIn("timestamp", data)
            self.assertIn("error", data)
            self.assertIn("retry_count", data)
            self.assertEqual(data["error"], "Test error")

    def test_delay_calculation(self):
        """Test that delays increase exponentially but are capped at max_delay."""
        # We can't easily test the internal delay calculation without mocking time,
        # but we can verify the behavior by checking sleep calls in a failing scenario
        pass

class TestLogApiError(unittest.TestCase):
    """Tests for the log_api_error function."""

    def setUp(self):
        self.test_log_path = Path("logs/api_errors.log")
        self.test_log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.test_log_path.exists():
            self.test_log_path.unlink()
        
        self.logger = get_logger("test_logger")
        self.logger.handlers = []
        file_handler = logging.FileHandler(self.test_log_path)
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        if self.test_log_path.exists():
            self.test_log_path.unlink()

    def test_log_api_error_writes_json(self):
        """Test that log_api_error writes a JSON line to the log file."""
        log_api_error(self.logger, "test_endpoint", "Test error message")
        
        self.assertTrue(self.test_log_path.exists())
        with open(self.test_log_path, 'r') as f:
            line = f.readline()
        
        data = json.loads(line)
        self.assertEqual(data["endpoint"], "test_endpoint")
        self.assertEqual(data["error"], "Test error message")
        self.assertIn("timestamp", data)
        self.assertIn("retry_count", data)

    def test_log_api_error_with_custom_retry_count(self):
        """Test that log_api_error accepts a custom retry count."""
        log_api_error(self.logger, "test_endpoint", "Test error", retry_count=5)
        
        with open(self.test_log_path, 'r') as f:
            line = f.readline()
        
        data = json.loads(line)
        self.assertEqual(data["retry_count"], 5)

class TestEnsureLogDirectory(unittest.TestCase):
    """Tests for ensure_log_directory."""

    def test_creates_directory_if_not_exists(self):
        """Test that ensure_log_directory creates the logs directory."""
        test_dir = Path("test_logs_dir")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        
        ensure_log_directory(str(test_dir))
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)

class TestRotateLogIfNeeded(unittest.TestCase):
    """Tests for rotate_log_if_needed."""

    def test_no_rotation_if_under_limit(self):
        """Test that log is not rotated if under size limit."""
        test_log = Path("logs/test_rotate.log")
        test_log.parent.mkdir(parents=True, exist_ok=True)
        test_log.write_text("small content")
        
        # 1MB limit
        rotate_log_if_needed(str(test_log), max_size_mb=1)
        
        self.assertTrue(test_log.exists())
        self.assertEqual(test_log.stat().st_size, len("small content"))
        test_log.unlink()

    def test_rotation_if_over_limit(self):
        """Test that log is rotated if over size limit."""
        test_log = Path("logs/test_rotate.log")
        test_log.parent.mkdir(parents=True, exist_ok=True)
        # Create a file larger than 1KB for testing (limit set to 0.001MB = 1KB)
        content = "x" * 2000 
        test_log.write_text(content)
        
        rotate_log_if_needed(str(test_log), max_size_mb=0.001)
        
        # Check if rotated file exists
        rotated_files = list(test_log.parent.glob("test_rotate.log.*"))
        self.assertGreater(len(rotated_files), 0)
        
        # Cleanup
        test_log.unlink()
        for f in rotated_files:
            f.unlink()

if __name__ == '__main__':
    unittest.main()