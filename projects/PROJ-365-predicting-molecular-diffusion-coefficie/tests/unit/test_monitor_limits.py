"""
Unit tests for utils.monitor – verify that the limit‑enforcement logic works.
"""

import pytest

from utils.monitor import ResourceLimitExceeded, enforce_limits, run_with_limits


def test_time_limit():
    """The helper should raise when elapsed time exceeds the limit."""
    with pytest.raises(ResourceLimitExceeded) as exc:
        enforce_limits(elapsed_seconds=5.0, peak_memory_mb=10.0, time_limit=1.0, memory_limit=100.0)
    assert "time limit" in str(exc.value)


def test_memory_limit():
    """The helper should raise when memory usage exceeds the limit."""
    with pytest.raises(ResourceLimitExceeded) as exc:
        enforce_limits(elapsed_seconds=0.5, peak_memory_mb=200.0, time_limit=10.0, memory_limit=50.0)
    assert "memory limit" in str(exc.value)


def test_resource_limit_message():
    """When both limits are exceeded the message should contain both reasons."""
    with pytest.raises(ResourceLimitExceeded) as exc:
        enforce_limits(elapsed_seconds=20.0, peak_memory_mb=500.0, time_limit=5.0, memory_limit=100.0)
    msg = str(exc.value).lower()
    assert "time limit" in msg
    assert "memory limit" in msg


def test_run_with_limits_respects_time():
    """run_with_limits should raise if the wrapped function runs too long."""
    def long_sleep():
        import time
        time.sleep(0.3)

    # Use a tiny time limit to trigger the exception quickly.
    with pytest.raises(ResourceLimitExceeded) as exc:
        run_with_limits(long_sleep, time_limit=0.1, memory_limit=1024)
    assert "time limit" in str(exc.value)


def test_run_with_limits_respects_memory(monkeypatch):
    """run_with_limits should raise if reported memory exceeds the limit."""
    # Monkey‑patch psutil to report a huge memory usage.
    class DummyProcess:
        def memory_info(self):
            class Info:
                rss = 10 * 1024 * 1024 * 1024  # 10 GB
            return Info()

    monkeypatch.setattr("psutil.Process", lambda _: DummyProcess())

    def dummy():
        return "ok"

    # Set a low memory limit (e.g., 100 MB) to provoke the exception.
    with pytest.raises(ResourceLimitExceeded) as exc:
        run_with_limits(dummy, time_limit=10.0, memory_limit=100.0)
    assert "memory limit" in str(exc.value)