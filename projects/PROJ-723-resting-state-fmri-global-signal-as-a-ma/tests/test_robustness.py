"""
Unit tests for robustness module functionality.

Tests verify:
- Alpha sweep results match expected MAE variations
- Variance metric correlation is within ±0.05 of primary SD result
"""

import pytest
import numpy as np
import pandas as pd

# Import robustness module (will be implemented in T028)
try:
    from code.robustness import run_alpha_sweep, calculate_variance_metric_correlation
    ROBUSTNESS_AVAILABLE = True
except ImportError:
    ROBUSTNESS_AVAILABLE = False

@pytest.mark.skipif(not ROBUSTNESS_AVAILABLE, reason="robustness module not yet implemented")
def test_alpha_sweep_results():
    """Verify alpha sweep results match expected MAE variations."""
    # Create synthetic data
    np.random.seed(42)
    n_samples = 200
    X = np.random.normal(size=(n_samples, 5))
    y = X[:, 0] * 0.5 + np.random.normal(scale=0.5, size=n_samples)
    
    results = run_alpha_sweep(X, y, alphas=[0.01, 0.1, 1.0, 10.0])
    
    # MAE should vary with alpha (typically U-shaped curve)
    assert len(results) == 4, f"Expected 4 results, got {len(results)}"
    assert all('mae' in r for r in results), "All results should have MAE"
    
    # Check that MAE varies (not all identical)
    maes = [r['mae'] for r in results]
    assert len(set(maes)) > 1, "MAE should vary across alpha values"

@pytest.mark.skipif(not ROBUSTNESS_AVAILABLE, reason="robustness module not yet implemented")
def test_variance_metric_correlation():
    """Verify variance metric correlation is within ±0.05 of primary SD result."""
    # Create synthetic data with known correlation
    np.random.seed(42)
    n_samples = 200
    global_signal_sd = np.random.normal(size=n_samples)
    global_signal_var = global_signal_sd ** 2  # Variance is square of SD
    mwq_score = global_signal_sd * 0.3 + np.random.normal(scale=0.5, size=n_samples)
    
    # Calculate both correlations
    sd_corr = np.corrcoef(global_signal_sd, mwq_score)[0, 1]
    var_corr = calculate_variance_metric_correlation(global_signal_var, mwq_score)
    
    # Correlation should be similar (within ±0.05)
    diff = abs(sd_corr - var_corr)
    assert diff <= 0.05, \
        f"Correlation difference {diff} exceeds threshold 0.05 (sd={sd_corr}, var={var_corr})"
