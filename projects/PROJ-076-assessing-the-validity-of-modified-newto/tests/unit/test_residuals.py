"""
Unit tests for residual analysis functions.
"""
import numpy as np
import pytest
from residuals import calculate_residuals, block_bootstrap_permutation_test, holm_bonferroni_correction

def test_calculate_residuals():
    """Test residual calculation."""
    obs = np.array([10.0, 20.0, 30.0])
    pred = np.array([9.0, 21.0, 29.0])
    
    res = calculate_residuals(obs, pred)
    expected = np.array([1.0, -1.0, 1.0])
    
    np.testing.assert_array_almost_equal(res, expected)

def test_calculate_residuals_mismatch():
    """Test error on mismatched lengths."""
    with pytest.raises(ValueError):
        calculate_residuals(np.array([1.0, 2.0]), np.array([1.0]))

def test_holm_bonferroni_correction():
    """Test Holm-Bonferroni correction logic."""
    p_values = [0.01, 0.04, 0.03, 0.005]
    corrected = holm_bonferroni_correction(p_values)
    
    assert len(corrected) == len(p_values)
    # Corrected p-values should be >= original
    assert all(c >= p for c, p in zip(corrected, p_values))
    # Should be <= 1.0
    assert all(c <= 1.0 for c in corrected)

def test_block_bootstrap_basic():
    """Test bootstrap test runs without error."""
    res_mond = np.random.normal(0, 1, 100)
    res_nfw = np.random.normal(0.5, 1, 100)
    
    p_val = block_bootstrap_permutation_test(res_mond, res_nfw, n_iterations=10)
    
    assert 0.0 <= p_val <= 1.0
    assert not np.isnan(p_val)
