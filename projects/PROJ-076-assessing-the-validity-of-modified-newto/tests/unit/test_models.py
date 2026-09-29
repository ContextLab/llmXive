"""
Unit tests for model functions (MOND and NFW).
"""
import numpy as np
import pytest
from models.mond import mond_simple
from models.nfw import nfw_model, nfw_model_params, nfw_concentration_prior

def test_mond_simple_basic():
    """Test basic MOND simple function behavior."""
    r = np.array([1.0, 10.0, 50.0]) # kpc
    v_c = 200.0 # km/s
    m_l = 1.0
    
    v_pred = mond_simple(r, v_c, m_l)
    
    assert v_pred.shape == r.shape
    assert np.all(v_pred > 0)
    # At large r, MOND should approach constant velocity (flat curve)
    # But with simple model and M/L=1, it depends on the transition.
    # Just check no NaNs or infinities
    assert not np.any(np.isnan(v_pred))
    assert not np.any(np.issnp(v_pred))

def test_mond_m_l_sensitivity():
    """Test that changing M/L affects the prediction."""
    r = np.array([10.0])
    v_c = 100.0
    
    v_low = mond_simple(r, v_c, 0.5)
    v_high = mond_simple(r, v_c, 2.0)
    
    # Higher M/L should yield higher velocity
    assert v_high > v_low

def test_nfw_model_basic():
    """Test basic NFW model behavior."""
    r = np.array([1.0, 10.0, 50.0])
    params = nfw_model_params()
    v_c, c, rs, m_l, v_bary = params['p0']
    
    v_pred = nfw_model(r, v_c, c, rs, m_l, v_bary)
    
    assert v_pred.shape == r.shape
    assert np.all(v_pred > 0)
    assert not np.any(np.isnan(v_pred))

def test_nfw_concentration_prior():
    """Test concentration prior scaling."""
    c_small = nfw_concentration_prior(1e9) # Low mass
    c_large = nfw_concentration_prior(1e11) # High mass
    
    # Alpha is negative, so higher mass -> lower concentration
    assert c_small > c_large
