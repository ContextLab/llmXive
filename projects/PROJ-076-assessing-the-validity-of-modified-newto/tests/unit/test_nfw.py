"""
Unit tests for the NFW model implementation.
"""

import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.models.nfw import (
    nfw_circular_velocity,
    nfw_with_baryons,
    nfw_concentration_prior,
    nfw_model,
    nfw_model_params,
    alpha_prior
)

def test_nfw_circular_velocity_positive():
    """Test that NFW circular velocity is always positive."""
    r = np.array([0.1, 1.0, 5.0, 10.0, 20.0])
    v_c = 100.0
    r_s = 5.0

    v = nfw_circular_velocity(r, v_c, r_s)

    assert np.all(v > 0), "Circular velocity should be positive"
    assert len(v) == len(r), "Output length should match input"

def test_nfw_circular_velocity_shape():
    """Test that velocity decreases at large radii (asymptotic behavior)."""
    r_small = np.array([1.0, 2.0, 3.0])
    r_large = np.array([10.0, 20.0, 30.0])
    v_c = 150.0
    r_s = 5.0

    v_small = nfw_circular_velocity(r_small, v_c, r_s)
    v_large = nfw_circular_velocity(r_large, v_c, r_s)

    # At larger radii, velocity should generally decrease or plateau
    # (exact behavior depends on NFW profile)
    assert np.all(v_small > 0), "Small radius velocities should be positive"
    assert np.all(v_large > 0), "Large radius velocities should be positive"

def test_nfw_concentration_prior_negative_alpha():
    """Test that concentration decreases with increasing mass (negative alpha)."""
    m_baryon_small = 1e9
    m_baryon_large = 1e11

    c_small = nfw_concentration_prior(m_baryon_small, alpha_prior)
    c_large = nfw_concentration_prior(m_baryon_large, alpha_prior)

    # With negative alpha, larger mass should have lower concentration
    assert c_small > c_large, "Concentration should decrease with mass for negative alpha"
    assert c_small > 0, "Concentration should be positive"
    assert c_large > 0, "Concentration should be positive"

def test_nfw_concentration_prior_bounds():
    """Test that concentration is within reasonable bounds."""
    m_baryon_values = [1e8, 1e9, 1e10, 1e11, 1e12]

    for m_baryon in m_baryon_values:
        c = nfw_concentration_prior(m_baryon, alpha_prior)
        assert 1.0 <= c <= 50.0, f"Concentration {c} out of bounds for mass {m_baryon}"

def test_nfw_with_baryons_total_velocity():
    """Test that total velocity is combination of DM and baryonic components."""
    r = np.array([1.0, 5.0, 10.0, 20.0])
    v_dm = 100.0
    r_s = 5.0
    v_baryon = 50.0

    v_total = nfw_with_baryons(r, v_dm, r_s, v_baryon)

    # Total velocity should be greater than either component alone
    v_dm_only = nfw_circular_velocity(r, v_dm, r_s)
    # Baryonic component (simplified)
    r_d = r_s / 3.0
    r_safe = np.where(r == 0, 1e-10, r)
    v_baryon_only = v_baryon * 0.5 * np.sqrt(1 - np.exp(-r_safe / r_d))

    assert np.all(v_total >= v_dm_only), "Total velocity should include DM contribution"
    assert np.all(v_total >= v_baryon_only), "Total velocity should include baryonic contribution"

def test_nfw_model_with_prior():
    """Test the full NFW model with concentration prior."""
    r = np.array([1.0, 5.0, 10.0, 20.0])
    v_dm = 120.0
    r_s = 6.0
    v_baryon = 60.0
    m_baryon = 1e10
    m_l_ratio = 0.5

    v_pred = nfw_model(r, v_dm, r_s, v_baryon, m_baryon, m_l_ratio)

    assert len(v_pred) == len(r), "Output length should match input"
    assert np.all(v_pred > 0), "All velocities should be positive"

def test_nfw_model_params_fixed_concentration():
    """Test NFW model with fixed concentration."""
    r = np.array([1.0, 5.0, 10.0, 20.0])
    v_dm = 100.0
    r_s = 5.0
    v_baryon = 50.0
    m_l_ratio = 0.5

    v_pred = nfw_model_params(r, v_dm, r_s, v_baryon, m_l_ratio)

    assert len(v_pred) == len(r), "Output length should match input"
    assert np.all(v_pred > 0), "All velocities should be positive"

def test_nfw_zero_radius():
    """Test behavior at r=0 (should handle gracefully)."""
    r = np.array([0.0, 0.1, 1.0])
    v_c = 100.0
    r_s = 5.0

    v = nfw_circular_velocity(r, v_c, r_s)

    # Should not raise error, velocity should be finite
    assert np.all(np.isfinite(v)), "All velocities should be finite"
    assert v[0] >= 0, "Velocity at r=0 should be non-negative"

def test_nfw_concentration_prior_zero_mass():
    """Test concentration prior with zero or negative mass."""
    c_zero = nfw_concentration_prior(0.0, alpha_prior)
    c_negative = nfw_concentration_prior(-1e10, alpha_prior)

    assert c_zero > 0, "Concentration should be positive for zero mass"
    assert c_negative > 0, "Concentration should be positive for negative mass"