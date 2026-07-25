"""
Unit tests for statistical functions.
"""
import pytest
import numpy as np
from code.analyze_pvalues import calculate_ks_statistic
from code.run_tests import run_hypothesis_tests

def test_ks_statistic_uniform():
    """Test KS statistic calculation against uniform distribution."""
    # Generate uniform p-values
    np.random.seed(42)
    uniform_pvals = np.random.rand(1000)
    
    result = calculate_ks_statistic(uniform_pvals)
    
    # For uniform data, KS should be small
    assert result["KS_statistic"] < 0.1
    assert result["p_value"] > 0.05

def test_hypothesis_test_execution():
    """Test that hypothesis tests run without error on null data."""
    np.random.seed(123)
    data = np.random.randn(100, 10)
    
    pvals = run_hypothesis_tests(data, "t-test")
    
    assert len(pvals) == 10
    assert all(0 <= p <= 1 for p in pvals)
