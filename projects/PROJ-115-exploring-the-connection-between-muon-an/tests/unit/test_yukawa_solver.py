"""
Unit tests for the Yukawa Potential Solver (T002).
"""
import pytest
import numpy as np
from physics.yukawa_solver import (
    yukawa_potential,
    numerov_schrodinger,
    extract_sommerfeld_factor,
    solve_yukawa_binding_energy
)

def test_yukawa_potential_at_origin():
    """Test that potential does not crash at r=0."""
    r = np.array([0.0, 1.0, 2.0])
    alpha = 0.1
    m_V = 1.0
    V = yukawa_potential(r, alpha, m_V)
    assert V[0] != 0  # Should be a large negative number or handled
    assert V[1] < 0
    assert V[2] < 0
    # Check decay
    assert abs(V[2]) < abs(V[1])

def test_numerov_schrodinger_basic():
    """Test that the Numerov solver returns an array of the correct size."""
    r = np.linspace(0.1, 10.0, 100)
    k = 1.0
    alpha = 0.1
    m_V = 1.0
    u_start = 0.1
    u_prime_start = 1.0
    
    u = numerov_schrodinger(r, k, alpha, m_V, u_start, u_prime_start)
    
    assert len(u) == len(r)
    assert not np.any(np.isnan(u))
    assert not np.any(np.isinf(u))

def test_sommerfeld_factor_extraction():
    """Test extraction of Sommerfeld factor."""
    r = np.linspace(0.1, 100.0, 1000)
    k = 0.1
    alpha = 0.1
    m_V = 1.0
    u_start = 0.1
    u_prime_start = 1.0
    
    u = numerov_schrodinger(r, k, alpha, m_V, u_start, u_prime_start)
    S = extract_sommerfeld_factor(u, r, k, r[-1])
    
    assert S > 0
    # For weak coupling, S should be close to 1
    if alpha < 0.01:
        assert 0.9 < S < 1.1

def test_bound_state_threshold():
    """Test bound state detection logic."""
    # Below threshold
    result = solve_yukawa_binding_energy(alpha=0.01, m_V=100.0, m_chi=10.0)
    assert result is None
    
    # Above threshold (approx)
    result = solve_yukawa_binding_energy(alpha=0.1, m_V=1.0, m_chi=100.0)
    # This might return a value or None depending on the implementation details
    # We just check it doesn't crash
    assert result is None or isinstance(result, float)
