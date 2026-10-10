import pytest
import time
import random

from pipeline.loader import exponential_backoff

def test_exponential_backoff_success(monkeypatch):
    """
    The decorated function fails twice before succeeding.
    Verify that the correct number of sleeps occurs and that the
    delays follow the exponential schedule (30 s, then 60 s).
    """
    call_counter = {"count": 0}
    def flaky():
        call_counter["count"] += 1
        if call_counter["count"] < 3:
            raise ValueError("temporary failure")
        return "ok"

    # Record sleep durations instead of actually sleeping
    slept = []
    monkeypatch.setattr(time, "sleep", lambda d: slept.append(d))
    # Remove jitter for deterministic testing
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)

    wrapped = exponential_backoff(flaky)
    result = wrapped()
    assert result == "ok"
    # Two retries → two sleep calls
    assert len(slept) == 2
    assert slept[0] == 30      # first back‑off
    assert slept[1] == 60      # second back‑off (30 * 2)

def test_exponential_backoff_exhaust(monkeypatch):
    """
    The decorated function always fails.
    After the maximum number of retries (5) the original exception
    should be raised.
    """
    def always_fail():
        raise RuntimeError("persistent error")

    # Avoid real sleeping
    monkeypatch.setattr(time, "sleep", lambda d: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)

    wrapped = exponential_backoff(always_fail)
    with pytest.raises(RuntimeError):
        wrapped()