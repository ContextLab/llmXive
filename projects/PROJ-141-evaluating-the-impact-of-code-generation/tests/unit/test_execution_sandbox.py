"""
Unit tests for the Execution Sandbox module.

These tests verify timeout handling, crash handling, and error response generation
for the execution sandbox functionality.
"""

import os
import sys
import time
import unittest
import subprocess
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality.execution_sandbox import (
    execute_with_timeout,
    run_test_suite,
    create_error_response,
    log_execution_error,
    ExecutionTimeoutError,
    ExecutionCrashError,
    DEFAULT_TIMEOUT_SECONDS
)


class TestExecuteWithTimeout(unittest.TestCase):
    """Tests for the execute_with_timeout function."""

    def test_successful_execution(self):
        """Test successful command execution within timeout."""
        success, stdout, stderr, duration = execute_with_timeout(
            cmd=["echo", "Hello World"],
            timeout=10
        )
        
        self.assertTrue(success)
        self.assertIn("Hello World", stdout)
        self.assertGreaterEqual(duration, 0)
        self.assertLess(duration, 10)

    def test_execution_timeout(self):
        """Test timeout handling when command exceeds limit."""
        # Use a command that sleeps longer than timeout
        with self.assertRaises(ExecutionTimeoutError):
            execute_with_timeout(
                cmd=["sleep", "5"],
                timeout=1  # 1 second timeout
            )

    def test_non_zero_exit_code(self):
        """Test handling of non-zero exit codes."""
        success, stdout, stderr, duration = execute_with_timeout(
            cmd=["python", "-c", "import sys; sys.exit(1)"],
            timeout=10
        )
        
        self.assertFalse(success)
        self.assertIsNotNone(duration)

    def test_custom_timeout(self):
        """Test custom timeout value."""
        success, stdout, stderr, duration = execute_with_timeout(
            cmd=["echo", "Test"],
            timeout=30
        )
        
        self.assertTrue(success)
        self.assertLess(duration, 30)


class TestRunTestSuite(unittest.TestCase):
    """Tests for the run_test_suite function."""

    def test_successful_test_run(self):
        """Test successful test suite execution."""
        result = run_test_suite(
            submission_id="test-123",
            test_command=["echo", "Tests passed"],
            test_dir=os.getcwd(),
            timeout=10
        )
        
        self.assertEqual(result["submission_id"], "test-123")
        self.assertTrue(result["success"])
        self.assertIn("Tests passed", result["stdout"])
        self.assertIsNone(result["error_type"])

    def test_timeout_handling(self):
        """Test timeout error handling in test suite."""
        result = run_test_suite(
            submission_id="test-timeout",
            test_command=["sleep", "10"],
            test_dir=os.getcwd(),
            timeout=1
        )
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertIsNotNone(result["error_message"])

    def test_crash_handling(self):
        """Test crash error handling."""
        # This test verifies that unexpected errors are caught
        with patch('quality.execution_sandbox.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Unexpected crash")
            
            result = run_test_suite(
                submission_id="test-crash",
                test_command=["python", "-c", "print('test')"],
                test_dir=os.getcwd(),
                timeout=10
            )
            
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "CrashError")
            self.assertIsNotNone(result["traceback"])

    def test_result_structure(self):
        """Test that result dictionary has all required fields."""
        result = run_test_suite(
            submission_id="test-struct",
            test_command=["echo", "test"],
            test_dir=os.getcwd(),
            timeout=10
        )
        
        required_fields = [
            "submission_id", "timestamp", "timeout_seconds", "success",
            "error_type", "error_message", "traceback", "duration_seconds",
            "stdout", "stderr"
        ]
        
        for field in required_fields:
            self.assertIn(field, result)


class TestCreateErrorResponse(unittest.TestCase):
    """Tests for the create_error_response function."""

    def test_basic_error_response(self):
        """Test creation of basic error response."""
        response = create_error_response(
            submission_id="test-456",
            error_type="TimeoutError",
            error_message="Execution timed out"
        )
        
        self.assertFalse(response["success"])
        self.assertEqual(response["submission_id"], "test-456")
        self.assertEqual(response["error"]["type"], "TimeoutError")
        self.assertEqual(response["error"]["message"], "Execution timed out")
        self.assertIn("timestamp", response["error"])

    def test_error_response_with_traceback(self):
        """Test error response including traceback."""
        response = create_error_response(
            submission_id="test-789",
            error_type="CrashError",
            error_message="Unexpected crash",
            traceback_str="Traceback (most recent call last):\n  File..."
        )
        
        self.assertIn("traceback", response["error"])
        self.assertIn("Traceback", response["error"]["traceback"])

    def test_status_code_inclusion(self):
        """Test that status code is handled correctly."""
        response = create_error_response(
            submission_id="test-status",
            error_type="TimeoutError",
            error_message="Timeout",
            status_code=408
        )
        
        # Status code is used for logging but not included in response dict
        # The function returns the error structure
        self.assertEqual(response["error"]["type"], "TimeoutError")


class TestLogExecutionError(unittest.TestCase):
    """Tests for the log_execution_error function."""

    def test_error_logging(self):
        """Test that errors are logged correctly."""
        # This test mainly verifies the function doesn't crash
        log_execution_error(
            submission_id="test-log",
            error_type="TestError",
            error_message="Test message"
        )
        
        # If we reach here, the function executed without error

    def test_error_logging_with_traceback(self):
        """Test error logging with traceback."""
        log_execution_error(
            submission_id="test-log-2",
            error_type="TestError",
            error_message="Test message",
            traceback_str="Traceback..."
        )
        
        # Function should execute without error


class TestExecutionSandboxIntegration(unittest.TestCase):
    """Integration tests for the execution sandbox."""

    def test_real_python_execution(self):
        """Test execution of a real Python script."""
        result = run_test_suite(
            submission_id="integration-1",
            test_command=["python", "-c", "print('Integration test passed')"],
            test_dir=os.getcwd(),
            timeout=10
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Integration test passed", result["stdout"])

    def test_real_timeout_scenario(self):
        """Test a real timeout scenario."""
        result = run_test_suite(
            submission_id="integration-timeout",
            test_command=["python", "-c", "import time; time.sleep(10)"],
            test_dir=os.getcwd(),
            timeout=2
        )
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "TimeoutError")


if __name__ == "__main__":
    unittest.main()
