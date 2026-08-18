"""
Unit tests for the Inverse-Probability Weighting (IPW) estimator.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.estimators.ipw import estimate_ipw


@pytest.fixture
def complete_data():
    """
    Generate a complete dataset with known properties for IPW testing.
    """
    np.random.seed(42)
    n = 1000
    X = np.random.uniform(-1, 1, n)
    D = (X > 0).astype(int)
    Z = np.random.normal(0, 1, n)
    # True effect = 0.5
    epsilon = np.random.normal(0, 0.5, n)
    Y = 0.5 * X + 0.5 * D + 0.1 * Z + epsilon
    
    # Create missingness indicator R (1 = observed)
    # For this test, we create a pattern where missingness depends on X (MAR)
    # P(R=1) = 1 / (1 + exp(-0.5 * X)) -> higher X -> higher probability of being observed
    logit = -0.5 * X
    prob_obs = 1 / (1 + np.exp(-logit))
    R = np.random.binomial(1, prob_obs, n)
    
    df = pd.DataFrame({
        'X': X,
        'Y': Y,
        'Z': Z,
        'D': D,
        'R': R
    })
    return df, 0.5  # Return data and true effect


@pytest.fixture
def data_with_mcar_missing():
    """
    Generate data with MCAR missingness.
    """
    np.random.seed(123)
    n = 1000
    X = np.random.uniform(-1, 1, n)
    D = (X > 0).astype(int)
    Z = np.random.normal(0, 1, n)
    epsilon = np.random.normal(0, 0.5, n)
    Y = 0.5 * X + 0.5 * D + 0.1 * Z + epsilon
    
    # MCAR: Random 30% missing
    R = np.random.binomial(1, 0.7, n)
    
    df = pd.DataFrame({
        'X': X,
        'Y': Y,
        'Z': Z,
        'D': D,
        'R': R
    })
    return df, 0.5


def test_ipw_complete_data(complete_data):
    """
    Test IPW on data with no missingness (R=1 for all).
    IPW should return results similar to OLS on the full data.
    """
    data, true_effect = complete_data
    # Ensure all R=1
    data['R'] = 1
    
    result = estimate_ipw(data, true_effect=true_effect, bandwidth=0.5)
    
    assert result['converged'] is True, "IPW should converge on complete data"
    assert not np.isnan(result['estimate']), "Estimate should not be NaN"
    assert not np.isnan(result['se']), "SE should not be NaN"
    # The estimate should be close to the true effect (0.5)
    # Allow some tolerance due to random noise
    assert abs(result['estimate'] - true_effect) < 0.2, f"Estimate {result['estimate']} too far from true effect {true_effect}"


def test_ipw_with_missingness(data_with_mcar_missing):
    """
    Test IPW with MCAR missingness.
    """
    data, true_effect = data_with_mcar_missing
    
    result = estimate_ipw(data, true_effect=true_effect, bandwidth=0.5)
    
    assert result['converged'] is True, "IPW should converge with MCAR data"
    assert not np.isnan(result['estimate']), "Estimate should not be NaN"
    # With MCAR, IPW should correct the bias (though MCAR doesn't introduce bias in OLS, 
    # it reduces efficiency. IPW weights should be roughly equal).
    # We check that it runs without crashing and produces a reasonable number.
    assert abs(result['estimate']) < 2.0, "Estimate seems unreasonably large"


def test_ipw_insufficient_observed():
    """
    Test IPW when there are very few observed cases.
    """
    np.random.seed(999)
    n = 1000
    X = np.random.uniform(-1, 1, n)
    D = (X > 0).astype(int)
    Z = np.random.normal(0, 1, n)
    Y = 0.5 * X + 0.5 * D + 0.1 * Z + np.random.normal(0, 0.5, n)
    
    # Only 2 observed cases
    R = np.zeros(n, dtype=int)
    R[0] = 1
    R[1] = 1
    
    data = pd.DataFrame({
        'X': X, 'Y': Y, 'Z': Z, 'D': D, 'R': R
    })
    
    result = estimate_ipw(data, true_effect=0.5)
    
    assert result['converged'] is False
    assert np.isnan(result['estimate'])
    assert 'error' in result


def test_ipw_bandwidth_filtering():
    """
    Test that IPW correctly filters data based on bandwidth.
    """
    np.random.seed(555)
    n = 2000
    X = np.random.uniform(-10, 10, n) # Wide range
    D = (X > 0).astype(int)
    Z = np.random.normal(0, 1, n)
    Y = 0.5 * X + 0.5 * D + 0.1 * Z + np.random.normal(0, 0.5, n)
    R = np.ones(n, dtype=int) # All observed
    
    data = pd.DataFrame({'X': X, 'Y': Y, 'Z': Z, 'D': D, 'R': R})
    
    # Use a small bandwidth
    result = estimate_ipw(data, true_effect=0.5, bandwidth=0.2)
    
    assert result['converged'] is True
    # The estimate should still be close to 0.5 if the model is correct locally
    assert abs(result['estimate'] - 0.5) < 0.5 # Loose tolerance for small sample
    
    # Check n_obs is roughly correct (should be around 2 * bandwidth * n / range)
    # Range is 20, bandwidth 0.2 -> 0.4/20 = 2% -> ~40 points
    assert result['n_obs'] < n, "Bandwidth filtering should reduce sample size"
    
def test_ipw_non_convergence():
    """
    Test behavior when propensity model does not converge.
    (Hard to force without specific data, but we test the return structure)
    """
    # We simulate a case where the model might fail by providing extreme data
    np.random.seed(777)
    n = 100
    X = np.random.uniform(-1, 1, n)
    D = (X > 0).astype(int)
    Z = np.random.normal(0, 1, n)
    Y = 0.5 * X + 0.5 * D + 0.1 * Z + np.random.normal(0, 0.5, n)
    
    # Create a deterministic R that might cause separation issues
    # e.g., R=1 only when X > 0.9
    R = (X > 0.9).astype(int)
    
    data = pd.DataFrame({'X': X, 'Y': Y, 'Z': Z, 'D': D, 'R': R})
    
    # This might result in few observed or separation
    result = estimate_ipw(data, true_effect=0.5, bandwidth=0.5)
    
    # We don't assert convergence here because it depends on the specific solver behavior,
    # but we assert that it returns a valid dict structure
    assert isinstance(result, dict)
    assert 'estimate' in result
    assert 'se' in result
    assert 'converged' in result