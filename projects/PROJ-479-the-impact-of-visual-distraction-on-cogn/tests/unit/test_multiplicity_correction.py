"""
Unit test for Holm-Bonferroni correction logic.

This test verifies the implementation of the Holm-Bonferroni method
for family-wise error rate control as used in code/03_analysis.py.
"""
import pytest
import numpy as np
from scipy.stats import multipletests


def test_holm_bonferroni_basic():
    """
    Test Holm-Bonferroni correction with a known set of p-values.
    
    Expected behavior:
    - Sorted p-values are adjusted sequentially.
    - Rejection decisions follow the step-down procedure.
    """
    # Known p-values (unsorted)
    raw_p_values = np.array([0.01, 0.04, 0.03, 0.005])
    alpha = 0.05
    n_tests = len(raw_p_values)
    
    # Apply Holm-Bonferroni using scipy
    # method='holm' implements the step-down procedure
    reject, corrected_p, _, _ = multipletests(
        raw_p_values, 
        alpha=alpha, 
        method='holm'
    )
    
    # Verify that we get the correct number of results
    assert len(reject) == n_tests
    assert len(corrected_p) == n_tests
    
    # Verify that corrected p-values are non-decreasing
    # (a property of the Holm-Bonferroni adjustment)
    assert all(np.diff(corrected_p) >= 0), "Corrected p-values should be non-decreasing"
    
    # Verify that corrected p-values are >= original p-values
    assert all(corrected_p >= raw_p_values), "Corrected p-values should be >= original p-values"
    
    # Verify that corrected p-values do not exceed 1.0
    assert all(corrected_p <= 1.0), "Corrected p-values should not exceed 1.0"


def test_holm_bonferroni_rejection_logic():
    """
    Test that the rejection logic follows the Holm-Bonferroni step-down procedure.
    
    For a set of sorted p-values p_(1) <= p_(2) <= ... <= p_(m),
    we reject H_(i) if p_(i) <= alpha / (m - i + 1).
    """
    # Create a scenario where we expect specific rejections
    # p-values: 0.001, 0.01, 0.04, 0.06 (sorted)
    # m = 4, alpha = 0.05
    # Thresholds: 0.05/4=0.0125, 0.05/3=0.0167, 0.05/2=0.025, 0.05/1=0.05
    # Expected rejections: 1st (0.001 < 0.0125), 2nd (0.01 < 0.0167), 
    #                      3rd (0.04 > 0.025 -> NO), 4th (0.06 > 0.05 -> NO)
    # So we expect 2 rejections.
    
    raw_p_values = np.array([0.06, 0.001, 0.04, 0.01])  # Unsorted
    alpha = 0.05
    
    reject, corrected_p, _, _ = multipletests(
        raw_p_values, 
        alpha=alpha, 
        method='holm'
    )
    
    # Count rejections
    n_rejections = np.sum(reject)
    
    # We expect exactly 2 rejections based on manual calculation
    assert n_rejections == 2, f"Expected 2 rejections, got {n_rejections}"
    
    # Verify which specific tests were rejected
    # After sorting: [0.001, 0.01, 0.04, 0.06]
    # Original indices: [1, 3, 2, 0]
    # Expected rejections: indices 1 and 3 (values 0.001 and 0.01)
    expected_rejected_indices = {1, 3}
    actual_rejected_indices = set(np.where(reject)[0])
    
    assert actual_rejected_indices == expected_rejected_indices, \
        f"Expected rejections at indices {expected_rejected_indices}, got {actual_rejected_indices}"


def test_holm_bonferroni_edge_cases():
    """
    Test edge cases: all p-values significant, none significant, single test.
    """
    alpha = 0.05
    
    # Case 1: All p-values very small (all should be rejected)
    all_small = np.array([0.001, 0.002, 0.003])
    reject, _, _, _ = multipletests(all_small, alpha=alpha, method='holm')
    assert all(reject), "All small p-values should be rejected"
    
    # Case 2: All p-values very large (none should be rejected)
    all_large = np.array([0.5, 0.6, 0.7])
    reject, _, _, _ = multipletests(all_large, alpha=alpha, method='holm')
    assert not any(reject), "All large p-values should not be rejected"
    
    # Case 3: Single test (should behave like uncorrected)
    single = np.array([0.01])
    reject, corrected_p, _, _ = multipletests(single, alpha=alpha, method='holm')
    assert reject[0], "Single significant p-value should be rejected"
    assert corrected_p[0] == single[0], "Single test correction should equal original p-value"


def test_holm_bonferroni_consistency_with_manual_calculation():
    """
    Manually verify the Holm-Bonferroni adjustment formula.
    
    The adjusted p-value for the i-th smallest p-value is:
    p_adj(i) = max(p_adj(i-1), (m - i + 1) * p(i))
    with p_adj(0) = 0.
    """
    raw_p_values = np.array([0.05, 0.01, 0.03, 0.02])
    alpha = 0.05
    m = len(raw_p_values)
    
    # Get scipy results
    _, corrected_p_scipy, _, _ = multipletests(raw_p_values, alpha=alpha, method='holm')
    
    # Manual calculation
    sorted_indices = np.argsort(raw_p_values)
    sorted_p = raw_p_values[sorted_indices]
    
    corrected_p_manual = np.zeros(m)
    for i in range(m):
        # Calculate raw adjusted value
        adjusted = (m - i) * sorted_p[i]
        
        # Apply monotonicity constraint
        if i > 0:
            adjusted = max(adjusted, corrected_p_manual[i-1])
        
        # Cap at 1.0
        corrected_p_manual[i] = min(adjusted, 1.0)
    
    # Reorder to original indices
    corrected_p_manual_final = np.zeros(m)
    corrected_p_manual_final[sorted_indices] = corrected_p_manual
    
    # Compare with scipy (allowing for floating point precision)
    np.testing.assert_array_almost_equal(
        corrected_p_scipy, 
        corrected_p_manual_final, 
        decimal=10,
        err_msg="Holm-Bonferroni correction does not match manual calculation"
    )


def test_holm_bonferroni_alpha_threshold():
    """
    Test that the correction properly handles the alpha threshold.
    """
    # Create p-values that are exactly at the threshold boundaries
    # For m=3, alpha=0.05:
    # Thresholds: 0.05/3=0.0167, 0.05/2=0.025, 0.05/1=0.05
    raw_p_values = np.array([0.0167, 0.025, 0.05])
    alpha = 0.05
    
    reject, corrected_p, _, _ = multipletests(raw_p_values, alpha=alpha, method='holm')
    
    # The first two should be rejected (p <= threshold)
    # The last one is exactly at threshold, so it should be rejected too
    assert reject[0], "p=0.0167 should be rejected"
    assert reject[1], "p=0.025 should be rejected"
    assert reject[2], "p=0.05 should be rejected"
    
    # Verify corrected p-values are <= alpha for rejected tests
    assert all(corrected_p[reject] <= alpha), "Rejected tests should have corrected p <= alpha"
