import pytest
from memory_guard import MemoryGuard
from exceptions import MemoryLimitExceeded

def test_memory_guard_raises_when_usage_exceeds_threshold(monkeypatch):
    """
    Simulate memory usage that exceeds 90% of the configured limit
    and verify that MemoryLimitExceeded is raised on the appropriate
    iteration (when the guard is polled).
    """
    # Use a small check interval for the test to trigger the guard quickly.
    guard = MemoryGuard(limit_mb=100, check_interval=2)

    # Track how many times _usage_mb is called so we can return different
    # values on successive checks.
    call_counter = {"calls": 0}

    def fake_usage_mb():
        """
        First call (iteration 2) returns 95 MB, which is > 90% of 100 MB.
        Subsequent calls return 85 MB, which is below the threshold.
        """
        call_counter["calls"] += 1
        return 95 if call_counter["calls"] == 1 else 85

    # Patch the private method that reads RSS.
    monkeypatch.setattr(guard, "_usage_mb", fake_usage_mb)

    # Iteration 1 is not a multiple of check_interval; should do nothing.
    guard.check(iteration=1)  # No exception expected.

    # Iteration 2 triggers a check; usage is 95 MB → exceeds 90 MB.
    with pytest.raises(MemoryLimitExceeded):
        guard.check(iteration=2)

    # Iteration 4 triggers another check; usage now 85 MB → below threshold.
    # No exception should be raised.
    guard.check(iteration=4)  # Should pass silently.

def test_memory_guard_no_check_when_not_multiple(monkeypatch):
    """
    Ensure that the guard does not poll memory when the iteration count
    is not a multiple of the configured check_interval.
    """
    guard = MemoryGuard(limit_mb=100, check_interval=5)

    # If _usage_mb were called, we would raise an exception.
    def fail_if_called():
        raise AssertionError("_usage_mb should not be called for this iteration")

    monkeypatch.setattr(guard, "_usage_mb", fail_if_called)

    # Iteration 3 is not a multiple of 5; guard.check should simply return True.
    assert guard.check(iteration=3) is True