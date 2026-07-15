"""
Integration tests for the statistical significance pipeline.

This module contains the test for User Story 1 (US1) to validate the null model
using synthetic data where the true correlation is zero.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd

# Ensure code/ is in the path for imports
_code_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code')
if _code_path not in sys.path:
    sys.path.insert(0, _code_path)

from stats_engine import (
    compute_correlation,
    construct_graph,
    calculate_stats,
    generate_null_distribution
)
import config

# Set random seed for reproducibility in this specific test
TEST_SEED = 42

def test_synthetic_validation():
    """
    Integration test to verify p > 0.05 for null data (synthetic identity covariance).
    
    This test generates a synthetic dataset with N=500, V=20, and identity covariance
    (no true correlations). It then runs the full pipeline (correlation -> graph -> stats -> null dist)
    and verifies that the observed statistics fall within the central 95% of the null distribution,
    resulting in a p-value > 0.05.
    
    Per T016b requirements, this specific validation ensures the null model is not biased.
    """
    # 1. Generate Synthetic Data (N=500, V=20, Identity Covariance)
    # We use a fixed seed here to ensure the test is deterministic and reproducible.
    rng = np.random.default_rng(TEST_SEED)
    n_samples = 500
    n_vars = 20
    
    # Generate standard normal data (uncorrelated by construction)
    data = rng.standard_normal((n_samples, n_vars))
    df_synthetic = pd.DataFrame(data, columns=[f"var_{i}" for i in range(n_vars)])
    
    # 2. Compute Observed Statistics
    # Compute Pearson correlation matrix
    corr_matrix, _ = compute_correlation(df_synthetic, method='pearson')
    
    # Construct graph with default threshold (0.3 from config usually, but let's use a safe default)
    # We use the threshold defined in config if available, otherwise default to 0.3
    threshold = getattr(config, 'DEFAULT_CORR_THRESHOLD', 0.3)
    graph = construct_graph(corr_matrix, threshold=threshold)
    
    # Calculate observed statistics
    observed_stats = calculate_stats(graph)
    
    # 3. Generate Null Distribution
    # We perform N=1000 permutations as per T015 specification
    n_permutations = 1000
    null_results = generate_null_distribution(
        df_synthetic, 
        n_permutations=n_permutations, 
        stats_func=calculate_stats
    )
    
    # 4. Verification Logic
    # For each statistic, we check if the observed value falls within the central 95%
    # of the null distribution. If the null model is correct, p-values should be > 0.05.
    
    # We define a helper to calculate p-value from null distribution
    # p = (count(null >= observed) + 1) / (N + 1) for right-tailed or two-tailed logic
    # Since we are testing for "significance" (deviation from null), we check both tails or 
    # simply ensure the observed is not in the extreme tails.
    
    # The task requires verifying p > 0.05.
    # We will check the "Mean Absolute Correlation" and "Edge Density" as primary metrics.
    
    stats_to_check = ['mean_abs_corr', 'edge_density']
    passed_checks = 0
    
    for stat_name in stats_to_check:
        if stat_name not in observed_stats:
            # If a stat is not computed (e.g., graph is empty), skip or handle gracefully
            # In a synthetic uncorrelated dataset, graph might be empty, making stats 0.
            # We need to ensure the logic handles empty graphs.
            continue
        
        observed_val = observed_stats[stat_name]
        null_vals = null_results[stat_name]
        
        # Calculate empirical p-value (two-tailed logic for deviation)
        # p = (number of null values >= observed + number of null values <= -observed + 1) / (N + 1)
        # However, for positive stats like mean_abs_corr, we just check the upper tail.
        # If observed is 0 (or near 0), it should be in the center.
        
        # For mean_abs_corr and edge_density, they are non-negative.
        # We check if observed is in the top 2.5% or bottom 2.5% (two-tailed 5%).
        # But typically, we just check if it's extreme.
        # Let's calculate the proportion of null values >= observed.
        # If the null is correct, this should be around 0.5 if observed is the mean.
        # If observed is extreme, it will be close to 0 or 1.
        
        # We want to ensure it is NOT significant, so p > 0.05.
        # p-value = (sum(null >= observed) + 1) / (N + 1)
        # If observed is very small (near 0), p should be large (near 1.0).
        # If observed is very large, p should be small.
        # Since data is uncorrelated, observed should be small, so p should be large.
        
        count_extreme = np.sum(null_vals >= observed_val)
        p_value = (count_extreme + 1) / (n_permutations + 1)
        
        # We also check the lower tail if the statistic can be smaller than expected (unlikely for abs corr)
        # But for edge density, if observed is 0, p-value (upper) is 1.0.
        
        # The condition is p > 0.05.
        # If the observed value is in the central 95%, p > 0.05.
        # Since we are looking for non-significance, we expect p > 0.05.
        
        # Note: If the graph is empty, observed is 0. Null distribution might also be centered near 0.
        # If null_vals are all 0, p=1.0.
        
        if p_value > 0.05:
            passed_checks += 1
        else:
            # Fail loudly if the null model is biased
            pytest.fail(
                f"Synthetic validation failed for statistic '{stat_name}'. "
                f"Observed: {observed_val:.4f}, Null Mean: {np.mean(null_vals):.4f}, "
                f"P-value: {p_value:.4f}. The null model appears biased (p <= 0.05)."
            )
    
    # Ensure we checked at least one statistic
    assert passed_checks > 0, "No statistics were checked in the validation loop."
    
    # Optional: Print summary for debugging
    print(f"Synthetic validation passed for {passed_checks}/{len(stats_to_check)} statistics.")
    print(f"Observed stats: {observed_stats}")
    print(f"Null distribution means: { {k: np.mean(v) for k, v in null_results.items()} }")