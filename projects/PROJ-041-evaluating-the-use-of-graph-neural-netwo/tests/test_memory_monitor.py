"""
Tests for memory monitoring utilities (code/utils/memory_monitor.py).
"""

import pytest

from utils.memory_monitor import (
    MemoryLimitExceededError,
    run_with_limit,
    DEFAULT_MEMORY_LIMIT_MB,
)


def test_run_with_limit_raises_when_exceeding_hard_limit():
    """
    ``run_with_limit`` must raise ``MemoryLimitExceededError`` when the
    requested dummy allocation exceeds the hard 7 GB limit.
    """
    # The hard limit is defined by DEFAULT_MEMORY_LIMIT_MB (≈7 GB)
    hard_limit_gb = DEFAULT_MEMORY_LIMIT_MB / 1024

    # Request slightly more than the hard limit to trigger the error
    with pytest.raises(MemoryLimitExceededError):
        run_with_limit(limit_gb=hard_limit_gb + 0.1)


def test_run_with_limit_passes_when_within_limit():
    """
    ``run_with_limit`` should *not* raise when the dummy allocation is
    within the configured limit.
    """
    # Request well below the limit – should succeed silently
    run_with_limit(limit_gb=1.0)  # 1 GB, far under the 7 GB cap
