import pytest
import time
import sys
import os
from src.utils.timeout_utils import (
    TimeoutError, 
    TimeoutHandler, 
    enforce_api_timeout, 
    enforce_test_timeout,
    run_with_api_timeout,
    run_with_test_timeout
)

def test_timeout_handler_raises_timeout_error():
    """Test that a function exceeding the timeout raises TimeoutError."""
    # Only run this test on Unix-like systems where SIGALRM is available
    if not hasattr(pytest, 'skip') and not hasattr(__import__('signal'), 'SIGALRM'):
        pytest.skip("SIGALRM not supported on this platform")

    def slow_function():
        time.sleep(5)
        return "done"

    with pytest.raises(TimeoutError):
        TimeoutHandler.with_timeout(1, slow_function)

def test_timeout_handler_returns_success():
    """Test that a function completing within the timeout returns correctly."""
    def fast_function():
        time.sleep(0.1)
        return "success"

    result = TimeoutHandler.with_timeout(2, fast_function)
    assert result == "success"

def test_context_manager_timeout():
    """Test that the context manager enforces timeout."""
    if not hasattr(__import__('signal'), 'SIGALRM'):
        pytest.skip("SIGALRM not supported on this platform")

    with pytest.raises(TimeoutError):
        with TimeoutHandler.timeout_context(1):
            time.sleep(5)

def test_context_manager_success():
    """Test that the context manager allows success."""
    if not hasattr(__import__('signal'), 'SIGALRM'):
        pytest.skip("SIGALRM not supported on this platform")

    start = time.time()
    with TimeoutHandler.timeout_context(5):
        time.sleep(0.1)
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Should finish well before timeout

def test_api_timeout_decorator():
    """Test the 120s API timeout decorator."""
    if not hasattr(__import__('signal'), 'SIGALRM'):
        pytest.skip("SIGALRM not supported on this platform")

    @enforce_api_timeout
    def api_call():
        time.sleep(150) # Intentionally slow
        return "result"

    with pytest.raises(TimeoutError):
        api_call()

def test_test_timeout_decorator():
    """Test the 10s test timeout decorator."""
    if not hasattr(__import__('signal'), 'SIGALRM'):
        pytest.skip("SIGALRM not supported on this platform")

    @enforce_test_timeout
    def test_run():
        time.sleep(15) # Intentionally slow
        return "result"

    with pytest.raises(TimeoutError):
        test_run()

def test_api_timeout_helper_success():
    """Test run_with_api_timeout on a fast function."""
    def fast_api():
        time.sleep(0.1)
        return "ok"
    
    result = run_with_api_timeout(fast_api)
    assert result == "ok"

def test_test_timeout_helper_success():
    """Test run_with_test_timeout on a fast function."""
    def fast_test():
        time.sleep(0.1)
        return "ok"
    
    result = run_with_test_timeout(fast_test)
    assert result == "ok"