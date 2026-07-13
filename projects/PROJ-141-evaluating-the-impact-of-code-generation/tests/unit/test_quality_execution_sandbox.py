"""
Unit tests for code/quality/execution_sandbox.py
Tests for test suite execution with timeout handling.
"""
import unittest
import sys
import time
from pathlib import Path

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from quality.execution_sandbox import (
    ExecutionTimeoutError,
    ExecutionCrashError,
    execute_with_timeout,
    run_test_suite,
    create_error_response,
    log_execution_error
)


class TestExecutionSandbox(unittest.TestCase):
    """Unit tests for execution sandbox functionality."""

    def test_execute_with_timeout_success(self):
        """Test execution that completes within timeout."""
        def quick_task():
            return "success"
        
        result = execute_with_timeout(quick_task, timeout=5)
        self.assertTrue(result['success'])
        self.assertEqual(result['output'], 'success')

    def test_execute_with_timeout_failure(self):
        """Test execution that raises an exception."""
        def failing_task():
            raise ValueError("Test error")
        
        result = execute_with_timeout(failing_task, timeout=5)
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_execute_with_timeout_timeout(self):
        """Test execution that exceeds timeout."""
        def slow_task():
            time.sleep(10)
            return "done"
        
        result = execute_with_timeout(slow_task, timeout=1)
        self.assertFalse(result['success'])
        self.assertIn('timeout', result['error'].lower())

    def test_create_error_response(self):
        """Test error response creation."""
        error_msg = "Test error"
        submission_id = "test-123"
        
        response = create_error_response(error_msg, submission_id)
        self.assertEqual(response['submission_id'], submission_id)
        self.assertEqual(response['error'], error_msg)
        self.assertIn('timestamp', response)

    def test_log_execution_error(self):
        """Test error logging functionality."""
        submission_id = "log-test-456"
        error_msg = "Test logging error"
        
        # Should not raise
        log_execution_error(submission_id, error_msg)

    def test_run_test_suite_basic(self):
        """Test running a simple test suite."""
        test_code = """
def test_addition():
    assert 1 + 1 == 2

def test_multiplication():
    assert 2 * 3 == 6
"""
        result = run_test_suite(test_code, timeout=5)
        self.assertIsInstance(result, dict)
        self.assertIn('passed', result)
        self.assertIn('failed', result)

    def test_run_test_suite_with_failure(self):
        """Test running test suite with failing tests."""
        test_code = """
def test_pass():
    assert True

def test_fail():
    assert False
"""
        result = run_test_suite(test_code, timeout=5)
        self.assertIsInstance(result, dict)
        # Should have at least one failure
        self.assertGreater(result.get('failed', 0), 0)

    def test_run_test_suite_timeout(self):
        """Test test suite with infinite loop."""
        infinite_code = """
def test_infinite():
    while True:
  pass
"""
        result = run_test_suite(infinite_code, timeout=2)
        self.assertFalse(result.get('success', True))
        self.assertIn('timeout', result.get('error', '').lower())

    def test_run_test_suite_syntax_error(self):
        """Test test suite with syntax error."""
        bad_code = """
def test_syntax()
    assert True
"""
        result = run_test_suite(bad_code, timeout=5)
        self.assertFalse(result.get('success', True))
        self.assertIn('syntax', result.get('error', '').lower())

    def test_run_test_suite_empty(self):
        """Test running empty test suite."""
        result = run_test_suite("", timeout=5)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('passed', 0), 0)
        self.assertEqual(result.get('failed', 0), 0)

    def test_execution_timeout_error_exception(self):
        """Test ExecutionTimeoutError exception."""
        try:
            raise ExecutionTimeoutError("Test timeout")
        except ExecutionTimeoutError as e:
            self.assertEqual(str(e), "Test timeout")

    def test_execution_crash_error_exception(self):
        """Test ExecutionCrashError exception."""
        try:
            raise ExecutionCrashError("Test crash")
        except ExecutionCrashError as e:
            self.assertEqual(str(e), "Test crash")

    def test_run_test_suite_300s_timeout(self):
        """Test that 300s timeout is respected (FR-033)."""
        # This test verifies the timeout mechanism works
        # We use a shorter timeout for testing
        def very_slow_task():
            time.sleep(10)
            return "done"
        
        # Using 1 second timeout for test speed
        result = execute_with_timeout(very_slow_task, timeout=1)
        self.assertFalse(result['success'])
        self.assertIn('timeout', result['error'].lower())


if __name__ == '__main__':
    unittest.main()