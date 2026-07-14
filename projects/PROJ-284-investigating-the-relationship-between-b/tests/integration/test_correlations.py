"""
Integration tests for correlation analysis.
"""
import pytest
import numpy as np
import pandas as pd
from code.analysis.correlations import (
    compute_correlations,
    apply_fdr_correction
)

def test_correlation_with_synthetic_data():
    """
    Test correlation analysis on synthetic data with known ground truth.
    """
    # Create synthetic data with a known correlation
    n_subjects = 100
    np.random.seed(42)
    
    # Generate X (metric)
    X = np.random.randn(n_subjects)
    # Generate Y (behavior) with correlation r = 0.5
    Y = 0.5 * X + np.random.randn(n_subjects) * np.sqrt(1 - 0.5**2)
    
    # Create DataFrame
    df = pd.DataFrame({
        "subject_id": [f"sub_{i}" for i in range(n_subjects)],
        "metric": X,
        "behavior": Y,
        "fd": np.random.randn(n_subjects) * 0.1 # Small motion noise
    })
    
    # Run correlation
    results = compute_correlations(df, x_col="metric", y_col="behavior", covariate="fd")
    
    # Check that we got a result
    assert len(results) > 0, "No correlation results returned"
    
    # Check that the correlation is significant and positive (approx 0.5)
    # We allow some tolerance due to noise
    r_val = results.iloc[0]["r"]
    p_val = results.iloc[0]["p"]
    
    assert abs(r_val - 0.5) < 0.15, f"Expected r ~ 0.5, got {r_val}"
    assert p_val < 0.05, f"Expected p < 0.05, got {p_val}"

def test_fdr_correction():
    """
    Test FDR correction on a set of p-values.
    """
    # Create synthetic p-values
    # First 5 are significant (0.01), rest are not (0.5)
    p_values = [0.01] * 5 + [0.5] * 95
    
    # Apply FDR
    corrected = apply_fdr_correction(p_values)
    
    # Check that the first 5 are still significant (q < 0.05)
    # and the rest are not
    for i in range(5):
        assert corrected[i] < 0.05, f"Expected significant at index {i}, got q={corrected[i]}"
    
    for i in range(5, 100):
        assert corrected[i] >= 0.05, f"Expected non-significant at index {i}, got q={corrected[i]}"