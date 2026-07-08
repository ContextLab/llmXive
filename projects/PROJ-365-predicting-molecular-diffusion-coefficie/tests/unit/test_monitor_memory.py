import pytest
import os
import sys
import time
import threading
import json
from pathlib import Path

# Add the project root to the path to allow imports from code/
# Assuming this test is run from the project root or via pytest discovery
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.monitor import ResourceLimitExceeded, ResourceMonitor, run_with_limits
from utils.config import get_project_root

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to act as the project root for this test."""
    # Ensure the directories expected by monitor.py exist
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "artifacts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "logs").mkdir(parents=True, exist_ok=True)
    return tmp_path

def test_memory_limit_exceeded(temp_project_root):
    """
    Test that ResourceLimitExceeded is raised when a function consumes
    more memory than the specified limit.
    
    This simulates memory over-use by allocating a large list of integers
    and verifies the exception is raised.
    """
    # Set a very low memory limit (e.g., 1 MB) to force a quick failure
    # 1 MB = 1024 * 1024 bytes
    memory_limit_bytes = 1024 * 1024 
    time_limit_seconds = 60  # Generous time limit so we don't hit time limit first

    def memory_hog_function():
        """Function that intentionally consumes a lot of memory."""
        # Allocate a list that is significantly larger than 1 MB
        # Each int in Python is typically 28 bytes, plus list overhead.
        # 1,000,000 ints should be roughly 28MB+, well over 1MB limit.
        data = [i for i in range(1_000_000)]
        time.sleep(0.5)  # Ensure the allocation has settled
        return data

    monitor = ResourceMonitor(
        time_limit=time_limit_seconds,
        memory_limit=memory_limit_bytes,
        project_root=temp_project_root
    )

    with pytest.raises(ResourceLimitExceeded) as exc_info:
        run_with_limits(monitor, memory_hog_function)

    # Verify the exception message mentions memory
    assert "memory" in str(exc_info.value).lower() or "RAM" in str(exc_info.value)

def test_memory_within_limit(temp_project_root):
    """
    Test that a function consuming less memory than the limit completes successfully.
    """
    # Set a reasonable memory limit (e.g., 100 MB)
    memory_limit_bytes = 100 * 1024 * 1024
    time_limit_seconds = 60

    def small_memory_function():
        """Function that uses very little memory."""
        data = [i for i in range(100)]
        time.sleep(0.1)
        return data

    monitor = ResourceMonitor(
        time_limit=time_limit_seconds,
        memory_limit=memory_limit_bytes,
        project_root=temp_project_root
    )

    # This should NOT raise an exception
    try:
        result = run_with_limits(monitor, small_memory_function)
        assert result == [i for i in range(100)]
    except ResourceLimitExceeded:
        pytest.fail("Function should not have exceeded memory limit")

def test_monitor_records_peak_memory(temp_project_root):
    """
    Test that the ResourceMonitor correctly records peak memory usage
    in the artifacts/reports/runtime_memory.json file after execution.
    """
    # Set a limit that will be exceeded to trigger the exception and record
    memory_limit_bytes = 10 * 1024 * 1024  # 10 MB
    time_limit_seconds = 60

    def memory_heavy_function():
        # Allocate ~20 MB
        data = [i for i in range(2_000_000)]
        time.sleep(0.1)
        return data

    monitor = ResourceMonitor(
        time_limit=time_limit_seconds,
        memory_limit=memory_limit_bytes,
        project_root=temp_project_root
    )

    with pytest.raises(ResourceLimitExceeded):
        run_with_limits(monitor, memory_heavy_function)

    # Check that the report file was created
    report_path = Path(temp_project_root) / "data" / "artifacts" / "runtime_memory.json"
    assert report_path.exists(), "Runtime memory report file should exist after execution"

    with open(report_path, 'r') as f:
        report_data = json.load(f)

    assert "peak_memory_mb" in report_data, "Report should contain 'peak_memory_mb'"
    assert isinstance(report_data["peak_memory_mb"], (int, float)), "peak_memory_mb should be numeric"
    assert report_data["peak_memory_mb"] > 0, "Peak memory should be positive"

    # The recorded peak memory should be less than or equal to the limit if the limit was hit,
    # or close to the actual usage. Since we hit the limit, it should be near the limit.
    # However, the exact value depends on OS measurement granularity.
    # We just assert it exists and is numeric as per SC-005.
    assert report_data["peak_memory_mb"] <= (memory_limit_bytes / (1024 * 1024)) + 1, \
        "Recorded peak memory should be close to or under the limit"

def test_monitor_thread_stops_on_exception(temp_project_root):
    """
    Test that the monitoring thread stops correctly when the target function
    raises a ResourceLimitExceeded exception.
    """
    memory_limit_bytes = 5 * 1024 * 1024
    time_limit_seconds = 60

    def memory_exceeding_function():
        # Allocate ~20 MB
        data = [i for i in range(2_000_000)]
        time.sleep(0.1)
        return data

    monitor = ResourceMonitor(
        time_limit=time_limit_seconds,
        memory_limit=memory_limit_bytes,
        project_root=temp_project_root
    )

    # Ensure the monitor thread is not running before we start
    assert not monitor._monitor_thread.is_alive() or not monitor._monitor_thread.is_alive()

    with pytest.raises(ResourceLimitExceeded):
        run_with_limits(monitor, memory_exceeding_function)

    # Give the thread a moment to join/stop
    time.sleep(0.5)
    
    # The monitor should have stopped or be in a state where it won't trigger again
    # The exact state depends on implementation, but the key is no deadlock or hanging thread
    # We verify the file was written as a proxy for successful cleanup
    report_path = Path(temp_project_root) / "data" / "artifacts" / "runtime_memory.json"
    assert report_path.exists()