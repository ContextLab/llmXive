"""
Unit tests for the memory‑limit utilities (code/utils/memory_monitor.py).
"""

import pytest

from utils.memory_monitor import run_with_limit, MemoryLimitExceededError, memory_limit

def test_run_with_limit_raises_when_exceeding():
    """
    The helper should raise MemoryLimitExceededError if the requested
    dummy allocation exceeds the configured limit (default 7 GB).
    """
    # The default limit is 7 GB; request something larger.
    with pytest.raises(MemoryLimitExceededError):
        run_with_limit(limit_gb=memory_limit / 1024 + 0.1)  # just over the limit

def test_run_with_limit_passes_when_within_limit():
    """
    The helper should silently succeed when the request is within the limit.
    """
    # Request well below the default limit.
    run_with_limit(limit_gb=1.0)  # should not raise
