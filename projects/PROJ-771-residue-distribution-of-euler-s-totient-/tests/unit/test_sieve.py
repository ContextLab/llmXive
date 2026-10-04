"""
Unit tests for sieve module.
"""
import pytest
from sieve import compute_phi_linear_sieve, MemoryGuard

def test_phi_small_values():
    """Test phi(n) for small known values."""
    # phi(1)=1, phi(2)=1, phi(3)=2, phi(4)=2, phi(5)=4, phi(6)=2
    phi = compute_phi_linear_sieve(6)
    assert phi[1] == 1
    assert phi[2] == 1
    assert phi[3] == 2
    assert phi[4] == 2
    assert phi[5] == 4
    assert phi[6] == 2

def test_memory_guard_trigger(mocker):
    """Test memory guard trigger on high usage."""
    guard = MemoryGuard(limit_mb=100, check_interval=1)
    # Mock psutil to return high usage
    mocker.patch('psutil.virtual_memory', return_value=mocker.Mock(used=200*1024*1024, percent=95))
    assert guard.check(1) == False
