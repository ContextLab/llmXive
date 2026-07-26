"""
Unit tests for code/utils/timeout.py
"""
import pytest
import time
from utils.timeout import timeout_handler, enforce_timeout
from utils.logging import TimeoutError as PipelineTimeoutError

def test_timeout_handler_success():
    """Verify timeout_handler allows functions that complete in time."""
    @timeout_handler(timeout=5)
    def quick_function():
        time.sleep(0.1)
        return "success"
    
    result = quick_function()
    assert result == "success"

def test_timeout_handler_exceeds():
    """Verify timeout_handler raises error when time is exceeded."""
    @timeout_handler(timeout=0.1)
    def slow_function():
        time.sleep(1.0)
        return "should not reach"
    
    with pytest.raises(PipelineTimeoutError):
        slow_function()

def test_enforce_timeout_function():
    """Verify enforce_timeout raises error on timeout."""
    def slow_func():
        time.sleep(1.0)
        return "fail"
    
    with pytest.raises(PipelineTimeoutError):
        enforce_timeout(slow_func, timeout=0.1)