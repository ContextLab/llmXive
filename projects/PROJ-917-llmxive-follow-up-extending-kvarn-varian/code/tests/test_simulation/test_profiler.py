"""
Tests for simulation profiling logic.
"""
import pytest
import time

def test_profiling_overhead():
    """Verify profiler can measure time."""
    start = time.time()
    time.sleep(0.01)
    end = time.time()
    duration = end - start
    assert duration >= 0.01
    assert duration < 0.1  # Sanity check
