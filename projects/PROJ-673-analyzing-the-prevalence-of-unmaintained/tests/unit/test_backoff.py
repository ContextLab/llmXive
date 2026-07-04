"""
Unit tests for exponential backoff logic.
"""
import pytest
import time
from src.utils.backoff import exponential_backoff


def test_max_retries_enforced():
    """Test that the function stops after max_retries."""
    call_count = 0

    def failing_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        exponential_backoff(
            failing_func,
            max_retries=3,
            initial_delay=0.01,
            jitter=False
        )

    # Should be called max_retries + 1 times (initial + retries)
    assert call_count == 4


def test_successful_on_first_try():
    """Test that successful function returns immediately."""
    call_count = 0

    def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = exponential_backoff(success_func, max_retries=3)
    assert result == "success"
    assert call_count == 1


def test_delay_increases():
    """Test that delay increases with multiplier."""
    call_count = 0
    delays = []
    start_time = time.time()

    def failing_func():
        nonlocal call_count
        nonlocal start_time
        if call_count == 0:
            start_time = time.time()
        else:
            current_time = time.time()
            if call_count > 1:
                delays.append(current_time - start_time)
            start_time = current_time
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        exponential_backoff(
            failing_func,
            max_retries=3,
            initial_delay=0.1,
            multiplier=2.0,
            jitter=False
        )

    # Should have 3 delays recorded (after attempts 1, 2, 3)
    assert len(delays) == 3
    # Delays should be increasing (0.1, 0.2, 0.4)
    assert delays[0] > 0.09  # Allow small tolerance
    assert delays[1] > delays[0]
    assert delays[2] > delays[1]