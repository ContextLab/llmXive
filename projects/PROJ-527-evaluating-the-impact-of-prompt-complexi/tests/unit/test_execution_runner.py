"""
Unit tests for execution runner timeout handling.

This module implements the contract test for T021:
Verifying that the execution runner correctly handles timeouts,
marks samples as failed, and logs the appropriate error types.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path to allow imports from code/
# This mimics the environment when running via pytest from the root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

# Import the runner module to test
# We import the specific function we need to test
from execution.runner import run_code_with_timeout, ExecutionResult, ExecutionStatus


class TestTimeoutHandling:
    """Contract tests for timeout handling in the execution runner."""

    def test_timeout_marks_as_failed(self):
        """
        Contract: A code snippet that exceeds the timeout must be marked as FAILED.
        
        Given: A Python script that sleeps longer than the timeout threshold.
        When: run_code_with_timeout is executed with a short timeout.
        Then: The result status must be ExecutionStatus.FAILED and the error_type
              must indicate a timeout.
        """
        # Create a script that sleeps for 5 seconds
        slow_code = "import time; time.sleep(5)"
        
        # Run with a 1-second timeout
        result = run_code_with_timeout(slow_code, timeout=1)
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error_type == "TimeoutError"
        assert "timeout" in result.error_message.lower()

    def test_timeout_returns_correct_error_type(self):
        """
        Contract: The error_type field must explicitly identify 'TimeoutError'.
        
        This ensures downstream aggregation logic can filter by error type.
        """
        slow_code = "import time; time.sleep(10)"
        result = run_code_with_timeout(slow_code, timeout=0.5)
        
        assert result.error_type == "TimeoutError"

    def test_timeout_message_contains_duration(self):
        """
        Contract: The error message should include the timeout duration for debugging.
        """
        slow_code = "import time; time.sleep(2)"
        result = run_code_with_timeout(slow_code, timeout=1)
        
        assert result.error_message is not None
        assert "1" in result.error_message  # The timeout value should be in the message

    def test_fast_code_completes_successfully(self):
        """
        Contract: Code that finishes within the timeout must NOT be marked as failed.
        
        Given: A script that executes quickly.
        When: run_code_with_timeout is executed with a reasonable timeout.
        Then: The result status must be ExecutionStatus.SUCCESS (or PASSED if tests run).
              Note: Since we are just running code, not tests, we expect SUCCESS.
        """
        fast_code = "print('Hello')"
        result = run_code_with_timeout(fast_code, timeout=5)
        
        assert result.status != ExecutionStatus.FAILED
        assert result.error_type is None

    def test_syntax_error_handled_separately_from_timeout(self):
        """
        Contract: Syntax errors must be caught and marked with error_type='SyntaxError',
                distinct from TimeoutError.
        """
        bad_code = "print('Missing quote"
        result = run_code_with_timeout(bad_code, timeout=1)
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error_type == "SyntaxError"
        assert result.error_type != "TimeoutError"

    def test_runtime_exception_handled_separately_from_timeout(self):
        """
        Contract: Runtime exceptions (e.g., ZeroDivisionError) must be marked
                with their specific error type, not TimeoutError.
        """
        error_code = "1/0"
        result = run_code_with_timeout(error_code, timeout=5)
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error_type == "ZeroDivisionError"
        assert result.error_type != "TimeoutError"

    def test_timeout_does_not_hang(self):
        """
        Contract: The runner must not hang indefinitely even if the child process
                refuses to terminate (though our implementation uses subprocess with
                timeout which should handle this).
        """
        # This test ensures the parent process returns within a reasonable time
        start = time.time()
        slow_code = "import time; time.sleep(100)"
        result = run_code_with_timeout(slow_code, timeout=1)
        elapsed = time.time() - start
        
        # Should return in ~1 second, not 100
        assert elapsed < 5.0
        assert result.status == ExecutionStatus.FAILED

    def test_multiple_timeout_calls_independence(self):
        """
        Contract: Sequential timeout calls must not interfere with each other.
        """
        for i in range(3):
            result = run_code_with_timeout("import time; time.sleep(5)", timeout=0.5)
            assert result.status == ExecutionStatus.FAILED
            assert result.error_type == "TimeoutError"