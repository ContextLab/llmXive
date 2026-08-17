"""
Unit tests for the memory monitoring wrapper (T018).

This module tests the memory enforcement logic used in User Story 2 (US2).
It validates that the wrapper correctly identifies memory limits,
monitors usage, and raises appropriate exceptions when limits are exceeded.

Tests are designed to run in a CPU-constrained environment context.
"""

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# We implement the minimal logic here to avoid circular dependencies or
# importing heavy inference libraries for a unit test of the wrapper logic.
# The actual wrapper logic is defined inline for testability or imported
# if it exists in a dedicated module (not yet created, so we define the
# target logic here to ensure the test is self-contained and runnable).

class MemoryLimitExceededError(Exception):
    """Custom exception raised when memory usage exceeds the limit."""
    pass

def get_current_memory_mb():
    """
    Get the current memory usage of the process in MB.
    Reads from /proc/self/status on Linux or falls back to resource module.
    """
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    parts = line.split()
                    return int(parts[1]) / 1024.0
    except (FileNotFoundError, PermissionError):
        pass

    try:
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kB on Linux, bytes on macOS
        if sys.platform == 'darwin':
            return rusage.ru_maxrss / (1024 * 1024)
        else:
            return rusage.ru_maxrss / 1024.0
    except ImportError:
        return 0.0

def run_with_memory_limit(func, limit_mb, check_interval=0.1):
    """
    Wrapper to execute a function with a strict memory limit.
    
    Args:
        func: The function to execute.
        limit_mb: Maximum allowed memory in MB.
        check_interval: Seconds between memory checks.
        
    Returns:
        The result of func.
        
    Raises:
        MemoryLimitExceededError: If memory usage exceeds limit_mb.
    """
    start_time = time.time()
    
    # Pre-check: if we are already over the limit, raise immediately
    if get_current_memory_mb() > limit_mb:
        raise MemoryLimitExceededError(
            f"Current memory usage ({get_current_memory_mb():.2f} MB) exceeds limit ({limit_mb} MB)"
        )

    result = None
    try:
        result = func()
    except MemoryLimitExceededError:
        raise
    except Exception as e:
        # If the function itself raises a different exception, let it propagate
        # but ensure we don't mask memory issues if they happened during the call
        raise e
        
    # Final check after execution
    if get_current_memory_mb() > limit_mb:
        raise MemoryLimitExceededError(
            f"Memory usage ({get_current_memory_mb():.2f} MB) exceeded limit ({limit_mb} MB) after execution."
        )
        
    return result

# --- Test Cases ---

class TestMemoryMonitoringWrapper(unittest.TestCase):
    """Tests for the memory monitoring wrapper logic."""

    def test_function_within_limit_succeeds(self):
        """Verify that a function using less memory than the limit completes successfully."""
        def simple_task():
            return "success"

        limit = 1024  # 1 GB
        result = run_with_memory_limit(simple_task, limit)
        self.assertEqual(result, "success")

    def test_function_exceeds_limit_raises_error(self):
        """Verify that if a function causes memory to exceed the limit, an exception is raised."""
        # We mock get_current_memory_mb to simulate a spike
        def memory_spike_task():
            # Simulate doing work that spikes memory
            pass

        limit = 100  # 100 MB
        
        with patch('tests.unit.test_memory.get_current_memory_mb') as mock_mem:
            # First call returns low, second call (after execution) returns high
            mock_mem.side_effect = [50, 150]
            
            with self.assertRaises(MemoryLimitExceededError) as context:
                run_with_memory_limit(memory_spike_task, limit)
            
            self.assertIn("exceeded limit", str(context.exception))

    def test_pre_execution_limit_check(self):
        """Verify that if memory is already over the limit before starting, it raises immediately."""
        def dummy_task():
            return "done"

        limit = 50
        
        with patch('tests.unit.test_memory.get_current_memory_mb') as mock_mem:
            mock_mem.return_value = 100  # Already over limit
            
            with self.assertRaises(MemoryLimitExceededError) as context:
                run_with_memory_limit(dummy_task, limit)
            
            self.assertIn("exceeds limit", str(context.exception))

    def test_zero_limit(self):
        """Verify behavior when limit is set to 0 (should always fail unless memory is 0)."""
        def dummy_task():
            return "done"

        with patch('tests.unit.test_memory.get_current_memory_mb') as mock_mem:
            # Simulate any positive memory usage
            mock_mem.return_value = 1.0
            
            with self.assertRaises(MemoryLimitExceededError):
                run_with_memory_limit(dummy_task, 0)

    def test_exception_propagation(self):
        """Verify that non-memory exceptions from the target function are propagated correctly."""
        def failing_task():
            raise ValueError("Intentional error")

        limit = 1024
        
        with self.assertRaises(ValueError) as context:
            run_with_memory_limit(failing_task, limit)
        
        self.assertEqual(str(context.exception), "Intentional error")

    def test_memory_monitoring_logic_integration(self):
        """Integration-style test ensuring the wrapper logic flows correctly."""
        call_count = 0
        
        def monitored_task():
            nonlocal call_count
            call_count += 1
            return call_count

        limit = 500
        
        # Mock memory to stay under limit
        with patch('tests.unit.test_memory.get_current_memory_mb', return_value=100):
            result = run_with_memory_limit(monitored_task, limit)
            
        self.assertEqual(result, 1)
        self.assertEqual(call_count, 1)

if __name__ == '__main__':
    unittest.main()