import pytest
import numpy as np
from src.models.utils import benjamini_hochberg_fdr, bootstrap_confidence_interval, run_permutation_test_early_stop

def test_benjamini_hochberg_fdr():
    """Test FDR correction logic."""
    p_values = [0.01, 0.04, 0.03, 0.20, 0.15]
    significant, adjusted = benjamini_hochberg_fdr(p_values, alpha=0.05)
    
    assert len(significant) == len(p_values)
    assert len(adjusted) == len(p_values)
    # At least the smallest p-value should be significant
    assert significant[0] is True

def test_bootstrap_confidence_interval():
    """Test bootstrap CI calculation."""
    data = np.random.normal(0, 1, 1000)
    stat, lower, upper = bootstrap_confidence_interval(data, np.mean, n_bootstraps=100, seed=42)
    
    assert lower <= stat <= upper
    assert isinstance(stat, float)

def test_run_permutation_test_early_stop():
    """Test permutation test with early stop flag."""
    # Generate data with a known correlation
    np.random.seed(42)
    X = np.random.normal(0, 1, 100)
    y = X * 0.5 + np.random.normal(0, 0.5, 100)
    
    result = run_permutation_test_early_stop(y, X, n_shuffles=100, early_stop_check_interval=50, seed=42)
    
    assert "p_value" in result
    assert "n_shuffles" in result
    assert "early_stop_flag" in result
    assert "observed_statistic" in result
    assert result["n_shuffles"] == 100
    assert isinstance(result["p_value"], float)
    assert isinstance(result["early_stop_flag"], bool)

def test_run_permutation_test_full():
    """Test that full shuffles are completed."""
    np.random.seed(42)
    X = np.random.normal(0, 1, 50)
    y = np.random.normal(0, 1, 50)
    
    # Run with a small number for testing
    result = run_permutation_test_early_stop(y, X, n_shuffles=100, seed=42)
    
    assert result["n_shuffles"] == 100
    # Verify the flag logic doesn't stop execution
    assert "final_p_value" not in result or isinstance(result["p_value"], float)
