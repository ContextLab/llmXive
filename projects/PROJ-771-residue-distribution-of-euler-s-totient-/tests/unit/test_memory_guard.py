import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

import pytest
from memory_guard import MemoryGuard
from exceptions import MemoryLimitExceeded


def test_memory_guard_raises_when_usage_exceeds_threshold(monkeypatch):
    """
    Simulate memory usage that exceeds 90% of the configured limit
    and verify that MemoryLimitExceeded is raised on the appropriate
    iteration (when the guard is polled).
    """
    guard = MemoryGuard(limit_mb=100, check_interval=2)

    call_counter = {"calls": 0}

    def fake_usage_mb():
        call_counter["calls"] += 1
        return 95 if call_counter["calls"] == 1 else 85

    monkeypatch.setattr(guard, "_usage_mb", fake_usage_mb)

    # Iteration 1 is not a multiple of check_interval; no check.
    assert guard.check(iteration=1) is True

    # Iteration 2 triggers a check; usage 95 MB > 90 MB threshold.
    with pytest.raises(MemoryLimitExceeded):
        guard.check(iteration=2)

    # Iteration 4 triggers another check; usage 85 MB is fine.
    assert guard.check(iteration=4) is True


def test_memory_guard_no_check_when_not_multiple(monkeypatch):
    """
    The guard must not poll memory when the iteration count is not
    a multiple of the configured check_interval.
    """
    guard = MemoryGuard(limit_mb=100, check_interval=5)

    def fail_if_called():
        raise AssertionError("_usage_mb should not be called for this iteration")

    monkeypatch.setattr(guard, "_usage_mb", fail_if_called)

    assert guard.check(iteration=3) is True


def test_memory_guard_threshold_boundary(monkeypatch):
    """
    Usage exactly at 90% of the limit must NOT raise; usage just
    above must raise.
    """
    guard = MemoryGuard(limit_mb=100, check_interval=1)

    monkeypatch.setattr(guard, "_usage_mb", lambda: 90.0)
    assert guard.check(iteration=1) is True

    monkeypatch.setattr(guard, "_usage_mb", lambda: 90.5)
    with pytest.raises(MemoryLimitExceeded):
        guard.check(iteration=1)


def test_memory_guard_exception_is_not_type_error(monkeypatch):
    """
    Regression test: the guard must raise MemoryLimitExceeded
    itself, never a TypeError from a mismatched constructor call.
    """
    guard = MemoryGuard(limit_mb=10, check_interval=1)
    monkeypatch.setattr(guard, "_usage_mb", lambda: 50.0)
    with pytest.raises(MemoryLimitExceeded) as excinfo:
        guard.check(iteration=1)
    assert not isinstance(excinfo.value, TypeError)
    assert str(excinfo.value)