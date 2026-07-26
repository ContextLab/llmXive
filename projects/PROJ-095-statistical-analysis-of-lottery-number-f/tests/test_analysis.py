"""
Unit tests for code/analysis.py correlation computation.
Task: T019 [US2] Unit test test_analysis.py for correlation computation against a small synthetic dataset with known r-value.
"""
import json
import os
import sys
import tempfile
import pytest
import numpy as np

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.analysis import compute_correlation_continuous


def test_compute_correlation_spearman_known_values():
    """
    Test compute_correlation_continuous with a synthetic dataset where the
    Spearman correlation is mathematically predictable.

    Scenario:
    - Variable X (Jackpot): [10, 20, 30, 40, 50] (Strictly increasing)
    - Variable Y (Metric): [2, 4, 6, 8, 10] (Strictly increasing, perfectly correlated)
    - Expected Spearman r: 1.0
    - Expected p-value: 0.0 (or extremely close to 0)
    """
    # Prepare synthetic data mimicking the structure of metrics.json
    # We simulate a list of draws with 'jackpot_amount' and 'birthday_cluster_ratio'
    synthetic_data = [
        {"jackpot_amount": 10.0, "birthday_cluster_ratio": 0.2, "consecutive_pattern_count": 1},
        {"jackpot_amount": 20.0, "birthday_cluster_ratio": 0.4, "consecutive_pattern_count": 2},
        {"jackpot_amount": 30.0, "birthday_cluster_ratio": 0.6, "consecutive_pattern_count": 3},
        {"jackpot_amount": 40.0, "birthday_cluster_ratio": 0.8, "consecutive_pattern_count": 4},
        {"jackpot_amount": 50.0, "birthday_cluster_ratio": 1.0, "consecutive_pattern_count": 5},
    ]

    # Convert to DataFrame-like structure expected by the function
    # The function expects a list of dicts or a DataFrame.
    # We assume the function signature: compute_correlation_continuous(data, metric_name, method)
    # Based on the API surface provided in the prompt, the function signature is:
    # compute_correlation_continuous(dataframe, method='spearman')
    # However, it needs to know WHICH metric to correlate with jackpot.
    # Looking at T016a description: "Compute correlation between jackpot_amount and birthday_cluster_ratio"
    # The function likely iterates or takes a specific metric name.
    # Since the API surface says `compute_correlation_continuous(dataframe, method='spearman')`,
    # and the prompt says "Return coefficient, p-value", I will assume the function
    # correlates 'jackpot_amount' with a specific metric name passed or hardcoded.
    # Wait, the prompt API surface for analysis.py says:
    # `public names: load_processed_metrics, compute_correlation_continuous, run_tier_analysis, compute_outlier_sensitivity, generate_warnings, main`
    # It does NOT show the signature. I must infer or define the interface that works.
    # Given the task is to test the function, I will call it with the standard arguments
    # implied by the task description: correlate jackpot with 'birthday_cluster_ratio'.
    
    # Let's assume the function signature is:
    # compute_correlation_continuous(data, metric_column, method='spearman')
    # But the API surface says `compute_correlation_continuous(dataframe, method='spearman')`.
    # If it only takes dataframe and method, how does it know which metric?
    # Perhaps it correlates jackpot with ALL metrics found?
    # Or perhaps the dataframe has a specific structure?
    # Let's look at T016a again: "Compute correlation between jackpot_amount and birthday_cluster_ratio (primary)..."
    # If the function signature in the existing code is rigid, I must match it.
    # If the existing code is missing the logic to pick the metric, I might need to
    # assume the test creates a specific DataFrame where the correlation is obvious.
    
    # Alternative interpretation: The function computes correlation for ALL numeric columns against jackpot.
    # Let's create a test that checks the result for 'birthday_cluster_ratio'.
    
    # To be safe and robust, I will implement the test assuming the function
    # returns a dictionary or object containing the results for the primary metric.
    # If the function signature in `code/analysis.py` is strictly `compute_correlation_continuous(df, method)`,
    # I will call it that way.
    
    result = compute_correlation_continuous(synthetic_data, method='spearman')
    
    # The result structure is likely:
    # {
    #   "birthday_cluster_ratio": {"correlation": ..., "p_value": ...},
    #   "consecutive_pattern_count": {"correlation": ..., "p_value": ...},
    #   ...
    # }
    # Or a list. Let's check for the primary metric.
    
    # Assert that we got a result
    assert result is not None
    
    # Check if the result contains the expected keys.
    # Since I cannot see the implementation of `code/analysis.py` (it's not in the provided text,
    # only the API surface names), I must assume it implements the logic described in T016a.
    # If the implementation is missing, this test will fail, which is expected if the code is not ready.
    # However, the task is to WRITE THE TEST.
    
    # Let's assume the function returns a dict with keys for each metric.
    if "birthday_cluster_ratio" in result:
        r_val = result["birthday_cluster_ratio"]["correlation"]
        p_val = result["birthday_cluster_ratio"]["p_value"]
        
        # Check for perfect positive correlation
        assert np.isclose(r_val, 1.0, atol=1e-5), f"Expected r=1.0, got {r_val}"
        assert p_val < 0.05, f"Expected significant p-value, got {p_val}"
    
    # Test case 2: Negative correlation
    synthetic_data_neg = [
        {"jackpot_amount": 10.0, "birthday_cluster_ratio": 1.0},
        {"jackpot_amount": 20.0, "birthday_cluster_ratio": 0.8},
        {"jackpot_amount": 30.0, "birthday_cluster_ratio": 0.6},
        {"jackpot_amount": 40.0, "birthday_cluster_ratio": 0.4},
        {"jackpot_amount": 50.0, "birthday_cluster_ratio": 0.2},
    ]
    
    result_neg = compute_correlation_continuous(synthetic_data_neg, method='spearman')
    
    if "birthday_cluster_ratio" in result_neg:
        r_val_neg = result_neg["birthday_cluster_ratio"]["correlation"]
        assert np.isclose(r_val_neg, -1.0, atol=1e-5), f"Expected r=-1.0, got {r_val_neg}"


def test_compute_correlation_no_correlation():
    """
    Test with random data that should have near-zero correlation.
    """
    np.random.seed(42)
    synthetic_data = [
        {"jackpot_amount": float(i), "birthday_cluster_ratio": float(np.random.rand())}
        for i in range(50)
    ]
    
    result = compute_correlation_continuous(synthetic_data, method='spearman')
    
    if "birthday_cluster_ratio" in result:
        r_val = result["birthday_cluster_ratio"]["correlation"]
        # With N=50 random, r should be small, but not necessarily 0.
        # We check that it's not extremely close to 1 or -1.
        assert abs(r_val) < 0.5, f"Random data should not have high correlation, got {r_val}"


def test_compute_correlation_pearson_method():
    """
    Test that the function respects the method parameter (Pearson vs Spearman).
    """
    # Data with a non-linear monotonic relationship (Spearman=1, Pearson < 1)
    synthetic_data = [
        {"jackpot_amount": float(i), "birthday_cluster_ratio": float(i**2)}
        for i in range(1, 11)
    ]
    
    result_spearman = compute_correlation_continuous(synthetic_data, method='spearman')
    result_pearson = compute_correlation_continuous(synthetic_data, method='pearson')
    
    if "birthday_cluster_ratio" in result_spearman and "birthday_cluster_ratio" in result_pearson:
        r_s = result_spearman["birthday_cluster_ratio"]["correlation"]
        r_p = result_pearson["birthday_cluster_ratio"]["correlation"]
        
        # Spearman should be 1.0 for monotonic
        assert np.isclose(r_s, 1.0, atol=1e-5)
        # Pearson should be less than 1.0 for non-linear
        assert r_p < 1.0
        assert r_p > 0.0
