import time
import pytest
from utils.rate_limiter import RateLimiter, exponential_backoff_with_retry, RateLimitError

def test_rate_limiter_basic():
    """Test basic rate limiting functionality."""
    limiter = RateLimiter(calls=2, period=1.0)  # 2 calls per second
    
    # First two calls should succeed immediately
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    
    # Third call should fail
    assert limiter.acquire() is False

def test_rate_limiter_wait():
    """Test that rate limiter allows calls after waiting."""
    limiter = RateLimiter(calls=1, period=0.1)  # 1 call per 0.1 seconds
    
    assert limiter.acquire() is True
    assert limiter.acquire() is False
    
    time.sleep(0.15)  # Wait for reset
    
    assert limiter.acquire() is True

def test_exponential_backoff_retry_success():
    """Test that exponential backoff retries on failure."""
    attempt_count = 0
    
    def failing_then_success():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RateLimitError("Rate limited")
        return "success"
    
    result = exponential_backoff_with_retry(failing_then_success, max_retries=5, base_delay=0.01)
    
    assert result == "success"
    assert attempt_count == 3

def test_exponential_backoff_max_retries():
    """Test that max retries are respected."""
    attempt_count = 0
    
    def always_fails():
        nonlocal attempt_count
        attempt_count += 1
        raise RateLimitError("Always limited")
    
    with pytest.raises(RateLimitError):
        exponential_backoff_with_retry(always_fails, max_retries=2, base_delay=0.001)
    
    assert attempt_count == 3  # Initial + 2 retries