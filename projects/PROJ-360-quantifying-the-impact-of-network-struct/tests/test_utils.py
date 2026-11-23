"""
Unit tests for ``code.utils``.
"""

import logging
import time
import random
import os

import numpy as np
import pytest

from code.utils import (
    setup_logging,
    retry_with_exponential_backoff,
    pin_seed,
    APIRateLimiter,
)


def test_setup_logging_default():
    """Calling ``setup_logging()`` should return a logger named ``llmXive``."""
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "llmXive"
    # Default level is INFO
    assert logger.level == logging.INFO
    # Should have exactly one handler (StreamHandler)
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_setup_logging_with_existing_logger():
    """Existing logger should be configured with the supplied level."""
    existing = logging.getLogger("my_logger")
    logger = setup_logging(existing, logging.DEBUG)
    assert logger is existing
    assert logger.level == logging.DEBUG
    # Handlers should be added only once
    handler_count = len(existing.handlers)
    # Calling again must not add duplicate handlers
    logger2 = setup_logging(existing, logging.ERROR)
    assert len(existing.handlers) == handler_count
    assert logger2.level == logging.ERROR


def test_setup_logging_level_only():
    """Calling with a single integer should set the default logger's level."""
    logger = setup_logging(logging.WARNING)
    assert logger.name == "llmXive"
    assert logger.level == logging.WARNING


def test_pin_seed_determinism():
    """After pinning the seed, ``random`` and ``numpy`` should be deterministic."""
    pin_seed(12345)
    # Check that the environment variable is set
    assert os.getenv("PYTHONHASHSEED") == "12345"

    # Produce a few values from both libraries
    rand_vals = [random.random() for _ in range(3)]
    np_vals = np.random.rand(3).tolist()

    # Re‑pin the same seed and verify the sequences match exactly
    pin_seed(12345)
    assert [random.random() for _ in range(3)] == rand_vals
    assert np.random.rand(3).tolist() == np_vals


def test_retry_with_exponential_backoff_success():
    """The decorator should retry a failing function and eventually succeed."""
    call_counter = {"count": 0}

    def flaky():
        call_counter["count"] += 1
        if call_counter["count"] < 3:
            raise ValueError("temporary failure")
        return "ok"

    wrapped = retry_with_exponential_backoff(flaky, max_retries=5, base_delay=0.01)
    result = wrapped()
    assert result == "ok"
    assert call_counter["count"] == 3


def test_retry_with_exponential_backoff_exhaustion():
    """If the function keeps failing, the decorator should raise the last exception."""
    def always_fail():
        raise RuntimeError("always fails")

    wrapped = retry_with_exponential_backoff(always_fail, max_retries=3, base_delay=0.01)
    with pytest.raises(RuntimeError):
        wrapped()


def test_api_rate_limiter_basic(monkeypatch):
    """APIRateLimiter should enforce the minimum delay between calls."""
    # Freeze time so we can control the flow
    base_time = 1_000_000.0

    times = [base_time]

    def fake_time():
        return times[0]

    monkeypatch.setattr(time, "time", fake_time)

    limiter = APIRateLimiter(min_delay_seconds=0.5)

    # First acquire – no previous request, should not sleep
    start = time.time()
    limiter.acquire()
    assert limiter._last_request_time == start

    # Advance time by only 0.2 s (less than the min_delay)
    times[0] += 0.2

    # The next acquire should cause a sleep of 0.3 s.
    # We'll patch ``time.sleep`` to just advance our fake clock.
    def fake_sleep(seconds):
        times[0] += seconds

    monkeypatch.setattr(time, "sleep", fake_sleep)

    limiter.acquire()
    # After acquire, the internal timestamp should have moved forward
    # by the full 0.5 s from the original request.
    assert pytest.approx(limiter._last_request_time, rel=1e-3) == base_time + 0.5