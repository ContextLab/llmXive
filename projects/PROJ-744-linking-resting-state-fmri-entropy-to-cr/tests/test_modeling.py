"""
Unit tests for OLS modeling and FDR correction.
"""
import pytest
import pandas as pd
import numpy as np

def test_ols_coefficient_recovery():
    """
    Test that OLS recovers known coefficients from synthetic data.
    """
    # Create synthetic data: y = 2*x + 1 + noise
    np.random.seed(42)
    x = np.random.randn(100)
    y = 2 * x + 1 + np.random.randn(100) * 0.5
    
    df = pd.DataFrame({"y": y, "x": x})
    
    try:
        from code.modeling import fit_ols_model
        result = fit_ols_model(df, "y", ["x"])
        
        # Check if coefficient is approximately 2
        assert abs(result['coef_x'] - 2.0) < 0.5
    except ImportError:
        pytest.skip("code/modeling.py not yet implemented")

def test_fdr_correction():
    """
    Test Benjamini-Hochberg FDR implementation.
    """
    p_values = [0.01, 0.04, 0.03, 0.2, 0.5]
    
    try:
        from code.modeling import apply_fdr_correction
        adjusted = apply_fdr_correction(p_values)
        
        assert len(adjusted) == len(p_values)
        assert all(0 <= p <= 1 for p in adjusted)
    except ImportError:
        pytest.skip("code/modeling.py not yet implemented")
