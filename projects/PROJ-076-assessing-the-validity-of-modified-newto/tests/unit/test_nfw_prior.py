"""
Unit tests for NFW model concentration prior logic.
"""
import numpy as np
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models.nfw import nfw_concentration_prior, nfw_prior_log_prob

def test_nfw_concentration_prior_positive_mass():
    """Test prior calculation with positive baryonic mass."""
    c = 10.0
    M_baryon = 1.0  # 1e10 Msun
    alpha = 0.24
    
    # Should return a finite log-probability
    log_prob = nfw_concentration_prior(c, M_baryon, alpha)
    assert np.isfinite(log_prob)
    # Since c matches expected (c_expected = 10 * (1)^0.24 = 10), log_prob should be 0 (max)
    assert np.isclose(log_prob, 0.0, atol=1e-6)

def test_nfw_concentration_prior_high_mass():
    """Test prior calculation with higher baryonic mass."""
    c = 5.0
    M_baryon = 100.0  # 1e12 Msun
    alpha = 0.24
    
    log_prob = nfw_concentration_prior(c, M_baryon, alpha)
    assert np.isfinite(log_prob)
    # Expected c should be higher for higher mass, so c=5 should have lower probability
    # Expected c = 10 * (100)^0.24 ≈ 10 * 3.0 = 30
    # c=5 is far from 30, so log_prob should be negative
    assert log_prob < 0

def test_nfw_concentration_prior_zero_mass():
    """Test prior calculation with near-zero mass."""
    c = 10.0
    M_baryon = 1e-10
    
    log_prob = nfw_concentration_prior(c, M_baryon, 0.24)
    assert np.isfinite(log_prob)

def test_nfw_prior_log_prob_integration():
    """Test the wrapper function nfw_prior_log_prob."""
    params = {'c': 10.0}
    M_baryon = 1.0
    
    log_prob = nfw_prior_log_prob(params, M_baryon)
    assert np.isfinite(log_prob)
    assert np.isclose(log_prob, 0.0, atol=1e-6)

def test_nfw_prior_invalid_concentration():
    """Test prior with invalid (negative) concentration."""
    c = -1.0
    M_baryon = 1.0
    
    log_prob = nfw_concentration_prior(c, M_baryon)
    # Should return -inf for invalid concentration
    assert log_prob == -np.inf