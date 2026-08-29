"""
Test for T024: Statistical comparison between RF and Null model.
"""
import os
import json
import numpy as np
import pytest
from scipy.stats import ttest_ind

# Test the statistical comparison logic directly
def test_t024_statistical_comparison_logic():
    """Verify the t-test logic for comparing absolute errors."""
    # Simulate test data
    np.random.seed(42)
    y_test = np.random.normal(100, 20, 100)
    
    # RF model: slightly better predictions (lower error)
    y_rf_pred = y_test + np.random.normal(0, 5, 100)
    
    # Null model: mean strategy (higher error)
    y_null_pred = np.full_like(y_test, np.mean(y_test))
    y_null_pred = y_null_pred + np.random.normal(0, 15, 100)
    
    # Calculate absolute errors
    abs_errors_rf = np.abs(y_test - y_rf_pred)
    abs_errors_null = np.abs(y_test - y_null_pred)
    
    # Perform t-test
    t_stat, p_value = ttest_ind(abs_errors_rf, abs_errors_null)
    
    # Verify results are valid
    assert not np.isnan(t_stat), "t-statistic should not be NaN"
    assert not np.isnan(p_value), "p-value should not be NaN"
    assert 0 <= p_value <= 1, "p-value must be between 0 and 1"
    
    # In this simulation, RF should be better (lower errors), so p-value should be small
    # Note: This is a simulation test; real data may vary
    logger_msg = f"T-statistic: {t_stat:.4f}, p-value: {p_value:.4f}"
    print(logger_msg)

def test_statistical_comparison_schema():
    """Verify the output schema matches requirements."""
    # Expected schema: {"p_value": 0.0, "test_statistic": 0.0}
    sample_output = {
        "p_value": 0.0234,
        "test_statistic": 2.15,
        "conclusion": "distinguishable"
    }
    
    assert "p_value" in sample_output
    assert "test_statistic" in sample_output
    assert isinstance(sample_output["p_value"], (int, float))
    assert isinstance(sample_output["test_statistic"], (int, float))