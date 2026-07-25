"""
Integration tests for statistical analysis.
"""
import pytest
import numpy as np
from code.generate_data import generate_correlated_data
from code.run_tests import run_hypothesis_tests
from code.analyze_pvalues import calculate_ks_statistic

def test_full_analysis_loop():
    """Test generating data, running tests, and analyzing p-values."""
    n, p = 2000, 50
    rho = 0.0
    seed = 777
    
    dataset = generate_correlated_data(n, p, rho, seed)
    pvals = run_hypothesis_tests(dataset.data, "t-test")
    
    ks_result = calculate_ks_statistic(np.array(pvals))
    
    assert "KS_statistic" in ks_result
    assert "p_value" in ks_result
