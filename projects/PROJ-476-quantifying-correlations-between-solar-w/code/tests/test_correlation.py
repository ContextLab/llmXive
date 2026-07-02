import pytest
import numpy as np
import pandas as pd
from scipy import signal
from code.analysis.neff import calculate_neff
from code.analysis.correlation import (
    compute_correlation_at_lag, 
    run_correlation_analysis,
    apply_bonferroni_correction,
    BONFERRONI_DIVISOR,
    ALPHA_ADJ
)
from code.config import ACE_VARS, NOAA_VARS

def test_correlation_bonferroni_divisor():
    """
    Verify that the Bonferroni divisor is derived dynamically from configuration.
    Expected: 3 params * 2 indices * 5 lags = 30.
    """
    # Check the constant is 30
    assert BONFERRONI_DIVISOR == 30, f"Expected divisor 30, got {BONFERRONI_DIVISOR}"
    
    # Verify the alpha adjustment calculation
    expected_alpha_adj = 0.05 / 30
    assert abs(ALPHA_ADJ - expected_alpha_adj) < 1e-9, f"Alpha adjustment mismatch"

def test_apply_bonferroni_correction():
    """Test that Bonferroni correction scales the p-value correctly."""
    p_val = 0.01
    corrected = apply_bonferroni_correction(p_val)
    expected = min(0.01 * 30, 1.0)
    assert abs(corrected - expected) < 1e-9
    
    # Test capping at 1.0
    p_val_large = 0.5
    corrected_large = apply_bonferroni_correction(p_val_large)
    assert corrected_large == 1.0

def test_compute_correlation_at_lag():
    """Test correlation calculation with synthetic data."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range(start='2000-01-01', periods=n, freq='h')
    
    # Create two correlated series
    x = np.random.randn(n)
    y = 0.8 * x + 0.1 * np.random.randn(n)
    
    series_x = pd.Series(x, index=dates)
    series_y = pd.Series(y, index=dates)
    
    r, rho, p = compute_correlation_at_lag(series_x, series_y, lag_hours=0)
    
    assert not np.isnan(r), "Correlation should not be NaN"
    assert abs(r - 0.8) < 0.1, f"Expected r ~ 0.8, got {r}"
    assert p < 0.05, "P-value should be significant"

def test_run_correlation_analysis_structure():
    """
    Verify that run_correlation_analysis returns a DataFrame with the correct columns
    and that it handles missing variables gracefully (though we assume full data here).
    """
    # Create a minimal synthetic dataset
    np.random.seed(42)
    n = 100
    dates = pd.date_range(start='1998-01-01', periods=n, freq='h')
    
    # Create data for all expected columns
    data = {
        'timestamp': dates,
        'N_p': np.random.randn(n),
        'T_p': np.random.randn(n),
        'He2+_ratio': np.random.randn(n),
        'Kp': np.random.randint(0, 9, n).astype(float),
        'Dst': np.random.randn(n) * 10
    }
    
    df = pd.DataFrame(data)
    
    # Run analysis
    results = run_correlation_analysis(df, train_start=1998, test_end=1998)
    
    expected_cols = [
        'param', 'index', 'lag', 'pearson_r', 'spearman_rho', 
        'raw_p', 'neff_adjusted_p', 'bonferroni_p', 'significant', 'neff'
    ]
    
    assert all(col in results.columns for col in expected_cols), "Missing expected columns"
    
    # Check that we have rows for all combinations (3 params * 2 indices * 5 lags = 30)
    # Note: This assumes all data is present and valid
    expected_rows = len(ACE_VARS) * len(NOAA_VARS) * 5
    assert len(results) == expected_rows, f"Expected {expected_rows} rows, got {len(results)}"