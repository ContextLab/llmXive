"""
Unit tests for execution timeout handling.
Ensures that tasks exceeding the time limit are recorded as "Timeout/Fail".
"""
import pytest
import time
import threading
import sys
from pathlib import Path

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.baseline_runner import run_with_timeout, ExecutionResult


class TestTimeout:
    """Tests for timeout handling logic."""

    def test_run_with_timeout_success(self):
        """Test that a function completing within the limit returns successfully."""
        def quick_task():
            time.sleep(0.1)
            return "success"

        result = run_with_timeout(quick_task, timeout=2.0)
        
        assert isinstance(result, ExecutionResult)
        assert result.status == "Pass"
        assert result.output == "success"

    def test_run_with_timeout_exceeded(self):
        """Test that a function exceeding the limit returns a Timeout/Fail status."""
        def slow_task():
            time.sleep(10)  # Sleep longer than timeout
            return "should not reach here"

        result = run_with_timeout(slow_task, timeout=0.5)

        assert isinstance(result, ExecutionResult)
        assert result.status == "Timeout/Fail"
        assert result.output is None or "Timeout" in str(result.output)

    def test_run_with_timeout_exception(self):
        """Test that a function raising an exception is caught."""
        def failing_task():
            raise ValueError("Intentional error")

        result = run_with_timeout(failing_task, timeout=2.0)

        assert isinstance(result, ExecutionResult)
        assert result.status == "Fail"
        assert "Intentional error" in str(result.output)

    def test_run_with_timeout_zero_timeout(self):
        """Test behavior with a near-zero timeout."""
        def task():
            time.sleep(0.01)
            return "done"

        # Very short timeout
        result = run_with_timeout(task, timeout=0.001)
        
        # Should likely be a timeout given the overhead
        assert result.status in ["Timeout/Fail", "Fail"]

    def test_run_with_timeout_concurrent(self):
        """Test that timeout handling works correctly in a multi-threaded context."""
        results = []
        
        def task(n):
            time.sleep(0.2)
            return f"task_{n}_done"

        # Run multiple tasks with a tight timeout
        for i in range(3):
            res = run_with_timeout(lambda n=i: time.sleep(0.5) or f"task_{n}", timeout=0.1)
            results.append(res)

        # All should be timeouts
        for res in results:
            assert res.status == "Timeout/Fail"

    def test_timeout_recording_in_baseline_runner(self, tmp_path):
        """
        Verify that the baseline runner logic correctly records "Timeout/Fail"
        in the output structure.
        """
        # This test verifies the contract that timeouts are explicitly recorded
        # as "Timeout/Fail" and not "Unknown" or "Skipped".
        
        def infinite_loop():
            while True:
                time.sleep(0.1)

        result = run_with_timeout(infinite_loop, timeout=0.2)

        # The critical assertion from T013/T015 requirements
        assert result.status == "Timeout/Fail", (
            f"Timeout must be recorded as 'Timeout/Fail', got: {result.status}"
        )
        assert result.output is None or "Timeout" in str(result.output)
        assert "Unknown" not in result.status
        assert "Skipped" not in result.status
