import pytest
import time
import os
import sys
import json
from pathlib import Path

# Adjust imports based on project structure
# Assuming tests are in tests/unit/ and code is in code/
# We need to add the code directory to the path
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from utils.monitor import ResourceLimitExceeded, ResourceMonitor, run_with_limits


def test_runtime_limit_exceeded():
    """
    Test that a function exceeding the time limit raises ResourceLimitExceeded.
    """
    # Create a monitor with a very short time limit (0.5 seconds)
    # and a high memory limit to avoid memory interference
    monitor = ResourceMonitor(time_limit=0.5, memory_limit=10000)
    
    # Define a dummy function that sleeps longer than the limit
    def slow_function():
        time.sleep(1.0)
        return "done"

    # Run the function with limits
    # We expect this to raise ResourceLimitExceeded
    with pytest.raises(ResourceLimitExceeded) as exc_info:
        run_with_limits(slow_function, monitor)

    # Verify the exception message mentions time limit
    assert "time" in str(exc_info.value).lower() or "timeout" in str(exc_info.value).lower()


def test_runtime_within_limit():
    """
    Test that a function completing within the time limit returns normally.
    """
    # Create a monitor with a generous time limit
    monitor = ResourceMonitor(time_limit=10.0, memory_limit=10000)
    
    # Define a function that completes quickly
    def fast_function():
        time.sleep(0.1)
        return "success"

    # Run the function with limits
    result = run_with_limits(fast_function, monitor)
    
    # Verify the function completed and returned the expected value
    assert result == "success"


def test_monitor_time_tracking():
    """
    Test that the monitor correctly tracks time even if no exception is raised.
    """
    monitor = ResourceMonitor(time_limit=10.0, memory_limit=10000)
    
    def timed_function():
        time.sleep(0.2)
        return 42

    # Start monitoring
    monitor.start()
    try:
        result = timed_function()
    finally:
        # Stop monitoring to record time
        monitor.stop()
    
    # Verify the recorded time is approximately correct (allowing for some overhead)
    assert 0.15 <= monitor.get_total_time() <= 0.5, f"Expected time around 0.2s, got {monitor.get_total_time()}"
    assert result == 42
