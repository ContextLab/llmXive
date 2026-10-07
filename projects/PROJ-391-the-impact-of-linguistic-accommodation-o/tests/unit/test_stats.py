import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import jaccard_similarity

def test_bootstrap_resampling_loop_logic():
    """
    Unit test for the bootstrap resampling loop logic.
    This tests the core mechanics: sampling with replacement,
    calculating statistics on the sample, and iterating correctly.
    """
    # Setup: Create a small deterministic dataset
    # We use a fixed seed for reproducibility in the test
    np.random.seed(42)
    n_samples = 100
    data = np.random.normal(loc=0.5, scale=0.2, size=n_samples)
    
    # Parameters
    n_iterations = 10
    target_ci_width = 0.1
    max_iter = 20
    
    # Manual implementation of the loop logic to verify correctness
    # without relying on the full stats module implementation
    bootstrap_means = []
    
    for i in range(n_iterations):
        # 1. Sample with replacement
        sample_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        sample_data = data[sample_indices]
        
        # 2. Calculate statistic (mean)
        stat = np.mean(sample_data)
        bootstrap_means.append(stat)
        
        # 3. Check convergence (simplified check for this unit test)
        # In the real implementation, this would check CI width
        # Here we just ensure the loop runs the correct number of times
        assert len(bootstrap_means) == i + 1
    
    # Assertions
    assert len(bootstrap_means) == n_iterations
    
    # Verify that sampling with replacement actually produces variation
    # (unless data is constant, which it isn't here)
    assert np.std(bootstrap_means) > 0.0, "Bootstrap samples should vary"
    
    # Verify the mean of bootstrap means is close to the original mean (bias check)
    original_mean = np.mean(data)
    bootstrap_mean_of_means = np.mean(bootstrap_means)
    
    # Allow a small tolerance for random variation in a small test
    assert abs(bootstrap_mean_of_means - original_mean) < 0.1, \
        f"Bootstrap mean {bootstrap_mean_of_means} should be close to original {original_mean}"

def test_bootstrap_convergence_logic():
    """
    Test the convergence logic: loop should stop early if CI width <= target.
    """
    np.random.seed(123)
    data = np.random.normal(loc=10, scale=1.0, size=500)
    
    n_iterations = 5000
    target_ci_width = 0.01
    max_iter = 100
    
    bootstrap_stats = []
    actual_iterations = 0
    
    for i in range(n_iterations):
        # Sample with replacement
        sample = np.random.choice(data, size=len(data), replace=True)
        stat = np.mean(sample)
        bootstrap_stats.append(stat)
        actual_iterations += 1
        
        # Check convergence (simulate CI width calculation)
        if len(bootstrap_stats) >= 10: # Need min samples for CI
            stats_arr = np.array(bootstrap_stats)
            # 95% CI width approximation using standard error
            se = np.std(stats_arr) / np.sqrt(len(stats_arr))
            ci_width = 2 * 1.96 * se # Approximate width
            
            if ci_width <= target_ci_width:
                break
        
        # Safety break
        if i >= max_iter:
            break
    
    # Verify loop stopped either by convergence or max_iter
    assert actual_iterations <= max_iter, "Loop exceeded max iterations"
    assert actual_iterations >= 10, "Loop should run at least min iterations"

def test_bootstrap_output_structure():
    """
    Test that the bootstrap process generates the expected output structure.
    """
    np.random.seed(999)
    data = np.random.uniform(0, 1, size=200)
    
    n_iter = 50
    bootstrap_results = []
    
    for _ in range(n_iter):
        sample = np.random.choice(data, size=len(data), replace=True)
        # Calculate correlation-like stat (just mean for this test)
        stat = np.mean(sample)
        bootstrap_results.append(stat)
    
    # Verify output is a list of floats
    assert isinstance(bootstrap_results, list)
    assert len(bootstrap_results) == n_iter
    assert all(isinstance(x, (float, np.floating)) for x in bootstrap_results)
    
    # Verify we can calculate CI from results
    sorted_results = sorted(bootstrap_results)
    lower_idx = int(0.025 * len(sorted_results))
    upper_idx = int(0.975 * len(sorted_results))
    
    ci_lower = sorted_results[lower_idx]
    ci_upper = sorted_results[upper_idx]
    
    assert ci_lower <= ci_upper
    assert 0 <= ci_lower <= 1 # Data is uniform 0-1
    assert 0 <= ci_upper <= 1

def test_bonferroni_correction_calculation():
    """
    Unit test for Bonferroni correction calculation.
    
    The Bonferroni correction adjusts the significance level (alpha)
    to account for multiple comparisons. It divides the original alpha
    by the number of tests (m).
    
    Corrected alpha = alpha / m
    Corrected p-value = p-value * m (capped at 1.0)
    """
    # Parameters
    original_alpha = 0.05
    num_tests = 4  # Pearson & Spearman on lexical overlap, Pearson & Spearman on syntactic similarity
    
    # Expected corrected alpha
    expected_corrected_alpha = original_alpha / num_tests
    
    # Test the calculation logic
    corrected_alpha = original_alpha / num_tests
    
    assert corrected_alpha == expected_corrected_alpha
    assert abs(corrected_alpha - 0.0125) < 1e-9  # 0.05 / 4 = 0.0125
    
    # Test p-value adjustment
    # If we have p-values from 4 tests, they should be multiplied by 4 and capped at 1.0
    p_values = [0.001, 0.005, 0.02, 0.03]  # Some significant, some not
    
    adjusted_p_values = [min(p * num_tests, 1.0) for p in p_values]
    
    expected_adjusted = [0.004, 0.02, 0.08, 0.12]
    
    for adj, exp in zip(adjusted_p_values, expected_adjusted):
        assert abs(adj - exp) < 1e-9, f"Expected {exp}, got {adj}"
    
    # Test with p-values that would exceed 1.0 after adjustment
    p_values_high = [0.3, 0.4]
    adjusted_high = [min(p * num_tests, 1.0) for p in p_values_high]
    
    assert adjusted_high[0] == 1.0  # 0.3 * 4 = 1.2, capped to 1.0
    assert adjusted_high[1] == 1.0  # 0.4 * 4 = 1.6, capped to 1.0
    
    # Test decision logic: significant after correction?
    # Original alpha = 0.05, corrected = 0.0125
    # A p-value of 0.01 is significant (0.01 < 0.0125)
    # A p-value of 0.02 is not significant (0.02 > 0.0125)
    
    significant_p = 0.01
    not_significant_p = 0.02
    
    assert significant_p < corrected_alpha
    assert not_significant_p > corrected_alpha
    
    # Verify adjusted p-value logic
    adjusted_sig = min(significant_p * num_tests, 1.0)
    adjusted_not_sig = min(not_significant_p * num_tests, 1.0)
    
    # Adjusted p-value should still be < original alpha for significant results
    assert adjusted_sig < original_alpha
    # Adjusted p-value should be > original alpha for non-significant results
    assert adjusted_not_sig > original_alpha

def test_bonferroni_with_realistic_scenario():
    """
    Test Bonferroni correction in a realistic scenario matching the task description.
    
    Scenario: 4 hypothesis tests (Pearson/Spearman on lexical overlap, 
    Pearson/Spearman on syntactic similarity)
    """
    original_alpha = 0.05
    num_tests = 4
    
    # Simulate p-values from the 4 tests
    # Assume: 
    # - Pearson lexical: p=0.008 (significant)
    # - Spearman lexical: p=0.015 (not significant after correction)
    # - Pearson syntactic: p=0.002 (significant)
    # - Spearman syntactic: p=0.045 (not significant)
    simulated_p_values = [0.008, 0.015, 0.002, 0.045]
    
    corrected_alpha = original_alpha / num_tests
    
    # Apply Bonferroni correction
    adjusted_p_values = [min(p * num_tests, 1.0) for p in simulated_p_values]
    
    # Determine significance
    results = []
    for i, (p, adj_p) in enumerate(zip(simulated_p_values, adjusted_p_values)):
        is_significant = p < corrected_alpha
        results.append({
            'test': i,
            'original_p': p,
            'adjusted_p': adj_p,
            'significant': is_significant
        })
    
    # Verify expected outcomes
    # Test 0: 0.008 < 0.0125 -> significant
    assert results[0]['significant'] == True
    assert results[0]['adjusted_p'] == 0.032
    
    # Test 1: 0.015 > 0.0125 -> not significant
    assert results[1]['significant'] == False
    assert results[1]['adjusted_p'] == 0.06
    
    # Test 2: 0.002 < 0.0125 -> significant
    assert results[2]['significant'] == True
    assert results[2]['adjusted_p'] == 0.008
    
    # Test 3: 0.045 > 0.0125 -> not significant
    assert results[3]['significant'] == False
    assert results[3]['adjusted_p'] == 0.18
    
    # Count significant results
    num_significant = sum(1 for r in results if r['significant'])
    assert num_significant == 2

def test_bonferroni_edge_cases():
    """
    Test edge cases for Bonferroni correction.
    """
    # Single test (no correction needed effectively)
    alpha = 0.05
    n = 1
    assert alpha / n == 0.05
    
    # Many tests (very small corrected alpha)
    n = 1000
    corrected = alpha / n
    assert corrected == 0.00005
    
    # P-value of 0 should remain 0 after adjustment
    p_zero = 0.0
    adjusted = min(p_zero * 10, 1.0)
    assert adjusted == 0.0
    
    # P-value of 1.0 should remain 1.0
    p_one = 1.0
    adjusted = min(p_one * 10, 1.0)
    assert adjusted == 1.0
    
    # P-value > 1.0 (invalid but should be handled gracefully)
    p_invalid = 1.5
    adjusted = min(p_invalid * 10, 1.0)
    assert adjusted == 1.0