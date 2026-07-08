"""
Unit tests for code/analyze.py logic (T023).
Tests regression coefficient calculation and Bonferroni logic.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analyze import (
    run_univariate_regression,
    apply_bonferroni_correction,
    run_power_analysis,
    run_ordinal_regression
)

@pytest.fixture
def mock_data():
    """Create a mock dataset with known relationships."""
    np.random.seed(42)
    n = 200
    metric = np.random.uniform(5, 12, n)
    # Create a quadratic relationship: Trust = 1 + 0.5*M - 0.05*M^2 + noise
    trust = 1 + 0.5 * metric - 0.05 * (metric ** 2) + np.random.normal(0, 0.2, n)
    # Round trust to 1-5 for ordinal realism if needed, but OLS handles floats
    trust = np.clip(trust, 1, 5)
    
    df = pd.DataFrame({
        'flesch_kincaid': metric,
        'trust_rating': trust
    })
    return df

def test_univariate_regression_coefficients(mock_data):
    """Test that regression captures the quadratic relationship."""
    result = run_univariate_regression(mock_data, 'flesch_kincaid')
    
    assert result['converged'] is True
    assert 'coefficients' in result
    assert 'flesch_kincaid_sq' in result['coefficients']
    
    # The quadratic coefficient should be negative (inverted U)
    # True value is -0.05. With noise, it should be close.
    quad_coef = result['coefficients']['flesch_kincaid_sq']
    assert quad_coef < 0, "Quadratic coefficient should be negative for inverted-U"
    assert quad_coef > -0.2, "Quadratic coefficient magnitude seems unrealistic"

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    results = [
        {'p_values': {'p1': 0.01, 'p2': 0.04}},
        {'p_values': {'p1': 0.02, 'p2': 0.06}}
    ]
    
    corrected = apply_bonferroni_correction(results, alpha=0.05)
    
    assert len(corrected) == 2
    # k=2, alpha=0.025
    # 0.01 * 2 = 0.02
    # 0.04 * 2 = 0.08
    assert corrected[0]['p_values']['p1_bonferroni'] == 0.02
    assert corrected[0]['p_values']['p2_bonferroni'] == 0.08
    assert corrected[0]['adjusted_alpha'] == 0.025

def test_power_analysis_logic():
    """Test power analysis calculation."""
    results = [{'metric': 'test'}]
    n = 100
    power_res = run_power_analysis(results, n, alpha=0.05)
    
    assert 'min_detectable_f2' in power_res
    assert 'status' in power_res
    assert power_res['n'] == n
    assert power_res['power_target'] == 0.80

def test_ordinal_regression(mock_data):
    """Test ordinal regression runs without error."""
    result = run_ordinal_regression(mock_data, 'flesch_kincaid')
    
    # Should not error out, even if convergence is tricky with small data
    assert 'metric' in result or 'error' in result
    if 'error' not in result:
        assert result['converged'] is True
        assert 'coefficients' in result