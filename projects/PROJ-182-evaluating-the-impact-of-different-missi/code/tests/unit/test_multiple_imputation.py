"""
Unit tests for Multiple Imputation (MICE) estimator.

Tests:
- Basic functionality with complete data
- Handling of missing data
- Convergence behavior
- Edge cases (all missing, no missing)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.estimators.multiple_imputation import estimate_multiple_imputation

@pytest.fixture
def complete_data():
    """Generate complete synthetic data without missing values."""
    np.random.seed(42)
    n = 500
    X = np.random.uniform(-1, 1, n)
    Z = np.random.normal(0, 1, n)
    D = (X > 0).astype(int)
    # True effect = 0.5
    epsilon = np.random.normal(0, 0.5, n)
    Y = 0.5 + 0.3 * X + 0.2 * Z + 0.5 * D + epsilon
    
    return pd.DataFrame({'Y': Y, 'X': X, 'Z': Z, 'D': D})

@pytest.fixture
def data_with_missing():
    """Generate data with MCAR missingness in Y."""
    np.random.seed(42)
    n = 500
    X = np.random.uniform(-1, 1, n)
    Z = np.random.normal(0, 1, n)
    D = (X > 0).astype(int)
    epsilon = np.random.normal(0, 0.5, n)
    Y = 0.5 + 0.3 * X + 0.2 * Z + 0.5 * D + epsilon
    
    # Introduce MCAR missingness (20%)
    mask = np.random.random(n) > 0.8
    Y[mask] = np.nan
    
    return pd.DataFrame({'Y': Y, 'X': X, 'Z': Z, 'D': D})

@pytest.fixture
def all_missing_data():
    """Generate data where Y is completely missing."""
    np.random.seed(42)
    n = 100
    X = np.random.uniform(-1, 1, n)
    Z = np.random.normal(0, 1, n)
    D = (X > 0).astype(int)
    
    return pd.DataFrame({'Y': [np.nan] * n, 'X': X, 'Z': Z, 'D': D})

def test_mice_complete_data(complete_data):
    """Test MICE with complete data (should still work)."""
    result = estimate_multiple_imputation(complete_data, true_effect=0.5, seed=42)
    
    assert not np.isnan(result['estimate']), "Estimate should not be NaN for complete data"
    assert not np.isnan(result['se']), "Std error should not be NaN for complete data"
    assert result['method'] == 'MICE'
    assert abs(result['bias']) < 0.5, "Bias should be reasonable for complete data"

def test_mice_with_missingness(data_with_missing):
    """Test MICE with missing data."""
    result = estimate_multiple_imputation(data_with_missing, true_effect=0.5, seed=42)
    
    assert not np.isnan(result['estimate']), "Estimate should not be NaN after imputation"
    assert not np.isnan(result['se']), "Std error should not be NaN after imputation"
    assert result['converged'] or result['n_imputed'] > 0, "Should have attempted imputation"

def test_mice_all_missing(all_missing_data):
    """Test MICE when Y is completely missing."""
    result = estimate_multiple_imputation(all_missing_data, true_effect=0.5)
    
    assert np.isnan(result['estimate']), "Estimate should be NaN when Y is completely missing"
    assert result['converged'] == False
    assert result['n_imputed'] == 0

def test_mice_missing_columns():
    """Test MICE with missing required columns."""
    incomplete_data = pd.DataFrame({'X': [1, 2, 3], 'Z': [1, 2, 3]})
    
    with pytest.raises(ValueError, match="Missing required columns"):
        estimate_multiple_imputation(incomplete_data, true_effect=0.5)

def test_mice_different_m_values(data_with_missing):
    """Test MICE with different numbers of imputations."""
    results = []
    for m in [3, 5, 10]:
        result = estimate_multiple_imputation(data_with_missing, true_effect=0.5, m=m, seed=42)
        results.append(result)
    
    # Estimates should be similar but not identical due to randomness
    estimates = [r['estimate'] for r in results]
    # They should be within a reasonable range of each other
    assert max(estimates) - min(estimates) < 1.0, "Estimates with different m should be similar"

def test_mice_seed_reproducibility(data_with_missing):
    """Test that MICE produces reproducible results with the same seed."""
    result1 = estimate_multiple_imputation(data_with_missing, true_effect=0.5, seed=123)
    result2 = estimate_multiple_imputation(data_with_missing, true_effect=0.5, seed=123)
    
    assert result1['estimate'] == result2['estimate'], "Results should be identical with same seed"
    assert result1['se'] == result2['se'], "Standard errors should be identical with same seed"

def test_mice_bias_calculation(data_with_missing):
    """Test that bias is correctly calculated."""
    true_effect = 0.5
    result = estimate_multiple_imputation(data_with_missing, true_effect=true_effect, seed=42)
    
    expected_bias = result['estimate'] - true_effect
    assert np.isclose(result['bias'], expected_bias), "Bias should be estimate - true_effect"