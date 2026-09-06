"""Unit tests for sieve.py functionality."""
import pytest
from sieve import compute_phi_linear_sieve, MemoryGuard


def test_compute_phi_small_values():
    """Verify phi(n) against known small values."""
    # Known values: phi(1)=1, phi(2)=1, phi(3)=2, phi(4)=2, phi(5)=4
    result = compute_phi_linear_sieve(5)
    expected = [1, 1, 2, 2, 4]
    assert result == expected, f"Expected {expected}, got {result}"


def test_memory_guard_init():
    """Test MemoryGuard initialization."""
    guard = MemoryGuard(limit_percent=90)
    assert guard.limit_percent == 90
    assert guard.limit_bytes is None


def test_memory_guard_check_no_overflow():
    """Test MemoryGuard check when usage is low."""
    guard = MemoryGuard(limit_percent=90)
    # This should not raise
    guard.check()
