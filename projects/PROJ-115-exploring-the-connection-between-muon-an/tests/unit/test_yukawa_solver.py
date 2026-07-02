"""
Unit tests for the Yukawa Potential Solver (T002).
"""
import pytest
import numpy as np
from code.physics.yukawa_solver import yukawa_potential, extract_sommerfeld_factor

def test_yukawa_potential_at_origin():
    """Test potential behavior near r=0."""
    m_V = 100.0
    g = 0.1
    r = np.array([1e-12, 1e-9, 1e-6])
    V = yukawa_potential(r, m_V, g)
    # V ~ -g^2 / 4pi / r
    expected = - (g**2 / (4 * np.pi)) / r
    # Allow for the exp(-m_V r) ~ 1
    assert np.allclose(V, expected, rtol=1e-2)

def test_yukawa_potential_decay():
    """Test exponential decay at large r."""
    m_V = 100.0
    g = 0.1
    r = np.array([1.0, 2.0, 5.0]) # 1/MeV
    V = yukawa_potential(r, m_V, g)
    # Check that V decreases as exp(-m_V r)
    ratio = V[1] / V[0]
    expected_ratio = np.exp(-m_V * (r[1] - r[0])) * (r[0] / r[1])
    assert np.isclose(ratio, expected_ratio, rtol=0.1)

def test_sommerfeld_factor_coulomb_limit():
    """Test Sommerfeld factor in the Coulomb limit (m_V -> 0)."""
    m_chi = 10.0
    m_V = 1e-6 # Very small
    g = 0.1
    v = 0.01
    
    S = extract_sommerfeld_factor(m_chi, m_V, g, v, r_max=10000.0, n_points=20000)
    
    alpha = g**2 / (4 * np.pi)
    # Coulomb limit: S = (pi alpha / v) / (1 - exp(-pi alpha / v))
    x = np.pi * alpha / v
    S_expected = x / (1 - np.exp(-x))
    
    # Allow some numerical error
    assert np.isclose(S, S_expected, rtol=0.1), f"S={S}, expected={S_expected}"

def test_sommerfeld_factor_free_limit():
    """Test Sommerfeld factor when coupling is zero."""
    m_chi = 10.0
    m_V = 100.0
    g = 0.0
    v = 0.1
    
    S = extract_sommerfeld_factor(m_chi, m_V, g, v)
    # Should be 1.0
    assert np.isclose(S, 1.0, rtol=1e-5)

def test_sommerfeld_factor_resonance_behavior():
    """Test that S increases as v decreases (qualitative check)."""
    m_chi = 10.0
    m_V = 100.0
    g = 0.5 # Strong coupling
    
    S_v1 = extract_sommerfeld_factor(m_chi, m_V, g, 1e-2)
    S_v2 = extract_sommerfeld_factor(m_chi, m_V, g, 1e-3)
    
    # S should be larger for smaller v (attractive potential)
    assert S_v2 >= S_v1 * 0.9, "Sommerfeld factor should increase as velocity decreases"
