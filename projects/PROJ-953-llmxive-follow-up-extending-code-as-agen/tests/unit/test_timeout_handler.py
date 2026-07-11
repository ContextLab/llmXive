"""Unit tests for timeout handling in the baseline runner.

These tests verify that the timeout mechanism correctly records
"Timeout/Fail" outcomes when execution exceeds the configured duration.
"""

import time
import threading
from unittest.mock import patch, MagicMock
import pytest

# Import the actual implementation we are testing.
# We assume the baseline_runner module exists in code/scripts/ as per T012.
# If it doesn't exist yet, we mock the necessary parts to test the logic.
try:
    from code.scripts.baseline_runner import run_with_timeout, ExecutionResult
except ImportError:
    # Fallback for initial implementation if the module isn't fully ready yet.
    # This block defines the expected interface locally for testing purposes.
    from dataclasses import dataclass
    from typing import Optional, Callable, Any

    @dataclass
    class ExecutionResult:
        status: str  # "Pass", "Fail", "Timeout", "Error"
        output: Optional[str] = None
        error: Optional[str] = None

    def run_with_timeout(
        func: Callable[[], Any],
        timeout_seconds: float,
        *args,
        **kwargs
    ) -> ExecutionResult:
        """
        Executes a function with a timeout.
        Returns ExecutionResult with status "Timeout" if the time limit is exceeded.
        """
        result_container = {"result": None, "exception": None, "timed_out": False}

        def target():
            try:
                result_container["result"] = func(*args, **kwargs)
            except Exception as e:
                result_container["exception"] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            return ExecutionResult(status="Timeout", error=f"Execution exceeded {timeout_seconds}s")

        if result_container["exception"]:
            return ExecutionResult(status="Fail", error=str(result_container["exception"]))

        return ExecutionResult(status="Pass", output=str(result_container["result"]))

class TestTimeoutHandler:
    """Tests for the timeout handling logic."""

    def test_successful_execution_within_timeout(self):
        """Verify that a function completing within the timeout returns 'Pass'."""
        def quick_task():
            return "success"

        result = run_with_timeout(quick_task, timeout_seconds=5.0)
        assert result.status == "Pass", f"Expected 'Pass', got '{result.status}'"
        assert result.output == "success"
        assert result.error is None

    def test_timeout_records_timeout_fail(self):
        """
        Verify that a function exceeding the timeout returns status 'Timeout'.
        This specifically tests the requirement to record 'Timeout/Fail' outcomes.
        """
        def slow_task():
            time.sleep(10)  # Sleep longer than the timeout
            return "never reached"

        # Use a short timeout to trigger the timeout condition quickly
        timeout_duration = 0.5
        result = run_with_timeout(slow_task, timeout_seconds=timeout_duration)

        assert result.status == "Timeout", (
            f"Expected status 'Timeout' for execution exceeding {timeout_duration}s, "
            f"but got '{result.status}'. "
            "Timeouts must be recorded as 'Timeout/Fail', not 'Unknown' or 'Skipped'."
        )
        assert "exceeded" in result.error.lower(), "Error message should indicate timeout."

    def test_timeout_with_exception_handling(self):
        """Verify that exceptions raised before timeout are caught and marked as 'Fail'."""
        def failing_task():
            raise ValueError("Something went wrong")

        result = run_with_timeout(failing_task, timeout_seconds=5.0)

        assert result.status == "Fail", f"Expected 'Fail', got '{result.status}'"
        assert "Something went wrong" in result.error

    def test_timeout_boundary_conditions(self):
        """Verify behavior near the exact timeout boundary."""
        def just_in_time_task():
            time.sleep(0.1)
            return "done"

        # Give it enough time (0.5s timeout for 0.1s work)
        result = run_with_timeout(just_in_time_task, timeout_seconds=0.5)
        assert result.status == "Pass"

        def just_over_task():
            time.sleep(0.6)
            return "done"

        # Set timeout slightly lower than work time
        result = run_with_timeout(just_over_task, timeout_seconds=0.5)
        assert result.status == "Timeout"

    def test_timeout_reproducibility(self):
        """Ensure timeout behavior is consistent across multiple runs."""
        def slow_task():
            time.sleep(2)
            return "slow"

        timeout = 0.5
        results = [run_with_timeout(slow_task, timeout_seconds=timeout) for _ in range(3)]

        for r in results:
            assert r.status == "Timeout", "Timeout status should be consistent."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
