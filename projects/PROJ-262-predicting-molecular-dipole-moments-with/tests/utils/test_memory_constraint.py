"""
Tests for the memory constraint utility.

The test deliberately sets an unrealistically low memory limit to trigger the
``MemoryError`` path.
"""

import pytest

# Import from the utils package we just created.
from utils.memory_constraint import check_memory_usage, MemoryError


def test_memory_limit_exceeded():
    """
    Verify that ``check_memory_usage`` raises ``MemoryError`` when the limit is
    lower than the actual process memory consumption.
    """
    # 0.0001 GB ≈ 100 KB – any realistic Python process will exceed this.
    with pytest.raises(MemoryError):
        check_memory_usage(0.0001)