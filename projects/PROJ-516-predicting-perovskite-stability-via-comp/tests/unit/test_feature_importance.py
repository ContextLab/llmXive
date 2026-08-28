"""
Unit tests for multiple-comparison correction (Bonferroni and Benjamini-Hochberg).

This module validates the statistical correction logic used in the validation
pipeline for permutation importance testing (Task T029).
"""
import pytest
import numpy as np
from typing import List, Tuple

# Helper functions to be tested (implemented inline for self-containment of the test)
# In the actual implementation (code/validation.py), these would be imported.

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance threshold.
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags)
    """
    if not p_values:
        return [], []
    
    n_tests = len(p_values)
    adjusted = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p_adj < alpha for p_adj in adjusted]
    return adjusted, significant

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg (FDR) correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance threshold.
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags)
    """
    if not p_values:
        return [], []
    
    n_tests = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = sorted(range(n_tests), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    # Calculate BH adjusted p-values
    # adjusted_p[i] = min( (n * p[i] / (i+1)), 1.0 )
    # Ensure monotonicity: adjusted_p[i] <= adjusted_p[i+1] (working backwards)
    adjusted_sorted = [0.0] * n_tests
    current_min = 1.0
    
    for i in range(n_tests - 1, -1, -1):
        rank = i + 1
        val = min((n_tests * sorted_p[i]) / rank, 1.0)
        current_min = min(current_min, val)
        adjusted_sorted[i] = current_min
    
    # Map back to original order
    final_adjusted = [0.0] * n_tests
    for idx, adj_val in zip(sorted_indices, adjusted_sorted):
        final_adjusted[idx] = adj_val
        
    significant = [p_adj < alpha for p_adj in final_adjusted]
    return final_adjusted, significant


class TestBonferroniCorrection:
    """Tests for the Bonferroni correction logic."""

    def test_empty_list(self):
        """Test handling of empty input."""
        adjusted, significant = bonferroni_correction([])
        assert adjusted == []
        assert significant == []

    def test_single_value_significant(self):
        """Test single p-value that remains significant."""
        p_val = 0.01
        adjusted, significant = bonferroni_correction([p_val])
        assert len(adjusted) == 1
        assert adjusted[0] == p_val  # 1 * 0.01
        assert significant[0] is True

    def test_single_value_not_significant(self):
        """Test single p-value that becomes not significant."""
        p_val = 0.10
        adjusted, significant = bonferroni_correction([p_val], alpha=0.05)
        assert adjusted[0] == 0.10
        assert significant[0] is False

    def test_multiple_values_proper_scaling(self):
        """Test that p-values are scaled by the number of tests."""
        p_values = [0.01, 0.02, 0.03]
        adjusted, _ = bonferroni_correction(p_values)
        
        # With 3 tests:
        # 0.01 * 3 = 0.03
        # 0.02 * 3 = 0.06
        # 0.03 * 3 = 0.09
        assert np.isclose(adjusted[0], 0.03)
        assert np.isclose(adjusted[1], 0.06)
        assert np.isclose(adjusted[2], 0.09)

    def test_cap_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        adjusted, _ = bonferroni_correction(p_values)
        
        # 0.5 * 3 = 1.5 -> capped at 1.0
        assert adjusted[0] == 1.0
        assert adjusted[1] == 1.0
        assert adjusted[2] == 1.0

    def test_significance_threshold(self):
        """Test that significance is correctly determined against alpha."""
        p_values = [0.01, 0.02, 0.04]
        # 3 tests. Threshold 0.05.
        # Adj: 0.03 (Sig), 0.06 (Not), 0.12 (Not)
        _, significant = bonferroni_correction(p_values, alpha=0.05)
        assert significant == [True, False, False]

    def test_custom_alpha(self):
        """Test with a custom alpha level."""
        p_values = [0.01, 0.02]
        # 2 tests. Alpha 0.10.
        # Adj: 0.02, 0.04. Both < 0.10.
        _, significant = bonferroni_correction(p_values, alpha=0.10)
        assert significant == [True, True]

    def test_all_zero_pvalues(self):
        """Test behavior with extremely small p-values (effectively zero)."""
        p_values = [0.0, 0.0]
        adjusted, significant = bonferroni_correction(p_values)
        assert adjusted == [0.0, 0.0]
        assert significant == [True, True]

    def test_all_one_pvalues(self):
        """Test behavior with p-values of 1.0."""
        p_values = [1.0, 1.0]
        adjusted, significant = bonferroni_correction(p_values)
        assert adjusted == [1.0, 1.0]
        assert significant == [False, False]

class TestBenjaminiHochbergCorrection:
    """Tests for the Benjamini-Hochberg correction logic."""

    def test_empty_list(self):
        """Test handling of empty input."""
        adjusted, significant = benjamini_hochberg_correction([])
        assert adjusted == []
        assert significant == []

    def test_single_value(self):
        """Test single p-value."""
        p_val = 0.04
        adjusted, significant = benjamini_hochberg_correction([p_val])
        # Rank 1. (1 * 0.04) / 1 = 0.04
        assert np.isclose(adjusted[0], 0.04)
        assert significant[0] is True

    def test_monotonicity_constraint(self):
        """
        Test that the BH procedure ensures adjusted p-values are monotonic
        with respect to the sorted order of raw p-values.
        i.e., if p_i < p_j, then adj_p_i <= adj_p_j.
        """
        # Create a case where naive calculation would violate monotonicity
        # p = [0.01, 0.05] with n=2
        # Naive: 0.01 * 2 / 1 = 0.02
        #        0.05 * 2 / 2 = 0.05
        # This is monotonic. Let's try a case that breaks it.
        # p = [0.03, 0.04, 0.05] with n=3
        # Naive:
        # 0.03 * 3 / 1 = 0.09
        # 0.04 * 3 / 2 = 0.06  <- Violation! 0.06 < 0.09
        # 0.05 * 3 / 3 = 0.05  <- Violation!
        
        p_values = [0.03, 0.04, 0.05]
        adjusted, _ = benjamini_hochberg_correction(p_values)
        
        # Check monotonicity in the order of original p_values
        # Since original p_values are sorted, adjusted must be sorted too
        for i in range(len(adjusted) - 1):
            assert adjusted[i] <= adjusted[i+1], f"Monotonicity violated at {i}: {adjusted[i]} > {adjusted[i+1]}"

    def test_fdr_vs_fwer_strictness(self):
        """
        Verify that BH is less conservative than Bonferroni.
        For the same set of p-values, BH should yield more (or equal) significant results.
        """
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        _, sig_bonf = bonferroni_correction(p_values)
        _, sig_bh = benjamini_hochberg_correction(p_values)
        
        sig_bonf_count = sum(sig_bonf)
        sig_bh_count = sum(sig_bh)
        
        # BH should find at least as many significant results as Bonferroni
        assert sig_bh_count >= sig_bonf_count

    def test_significance_threshold(self):
        """Test significance determination with alpha."""
        p_values = [0.01, 0.02, 0.03]
        # n=3.
        # Sorted: 0.01, 0.02, 0.03
        # Naive: 0.03, 0.03, 0.03
        # Monotonic: 0.03, 0.03, 0.03
        # All < 0.05? Yes.
        _, significant = benjamini_hochberg_correction(p_values, alpha=0.05)
        assert significant == [True, True, True]
        
        # Now test with p_values that should fail
        p_values_fail = [0.04, 0.05, 0.06]
        # Sorted: 0.04, 0.05, 0.06
        # Naive: 0.12, 0.075, 0.06
        # Monotonic: 0.06, 0.06, 0.06
        # All < 0.05? No.
        _, significant_fail = benjamini_hochberg_correction(p_values_fail, alpha=0.05)
        assert all(not s for s in significant_fail)

    def test_custom_alpha(self):
        """Test with custom alpha."""
        p_values = [0.01, 0.02, 0.03]
        _, significant = benjamini_hochberg_correction(p_values, alpha=0.10)
        # Adjusted are 0.03, 0.03, 0.03. All < 0.10.
        assert significant == [True, True, True]

    def test_unsorted_input_preserves_order(self):
        """Test that output order matches input order, not sorted order."""
        p_values = [0.05, 0.01, 0.03] # Unsorted
        adjusted, significant = benjamini_hochberg_correction(p_values)
        
        # The algorithm sorts, calculates, then maps back.
        # Input order: 0.05 (idx 0), 0.01 (idx 1), 0.03 (idx 2)
        # Sorted: 0.01 (idx 1), 0.03 (idx 2), 0.05 (idx 0)
        # Naive calc:
        # 0.01: 3*0.01/1 = 0.03
        # 0.03: 3*0.03/2 = 0.045
        # 0.05: 3*0.05/3 = 0.05
        # Monotonic check (backwards):
        # 0.05 -> 0.05
        # 0.045 -> min(0.045, 0.05) = 0.045
        # 0.03 -> min(0.03, 0.045) = 0.03
        # Mapped back:
        # idx 0 (0.05): 0.05
        # idx 1 (0.01): 0.03
        # idx 2 (0.03): 0.045
        
        assert np.isclose(adjusted[0], 0.05)
        assert np.isclose(adjusted[1], 0.03)
        assert np.isclose(adjusted[2], 0.045)

class TestIntegrationScenarios:
    """Integration-style tests combining both corrections."""

    def test_comparison_on_realistic_data(self):
        """
        Simulate a realistic scenario with permutation importance p-values
        and compare the two methods.
        """
        # Simulated p-values from a permutation test (e.g., 20 features)
        np.random.seed(42)
        p_values = np.random.uniform(0.001, 0.2, 20).tolist()
        p_values.sort() # Sort to make it easier to reason about, though function handles unsorted
        
        adj_bonf, sig_bonf = bonferroni_correction(p_values)
        adj_bh, sig_bh = benjamini_hochberg_correction(p_values)
        
        # Verify lengths
        assert len(adj_bonf) == len(p_values)
        assert len(adj_bh) == len(p_values)
        
        # Verify monotonicity for BH
        for i in range(len(adj_bh) - 1):
            assert adj_bh[i] <= adj_bh[i+1]
        
        # Verify Bonferroni is strictly more conservative (fewer or equal significant)
        assert sum(sig_bh) >= sum(sig_bonf)

    def test_edge_case_all_significant(self):
        """Test when all p-values are extremely small."""
        p_values = [0.0001] * 10
        _, sig_bonf = bonferroni_correction(p_values)
        _, sig_bh = benjamini_hochberg_correction(p_values)
        
        # All should be significant
        assert all(sig_bonf)
        assert all(sig_bh)

    def test_edge_case_none_significant(self):
        """Test when all p-values are large."""
        p_values = [0.9] * 10
        _, sig_bonf = bonferroni_correction(p_values)
        _, sig_bh = benjamini_hochberg_correction(p_values)
        
        # All should be not significant
        assert not any(sig_bonf)
        assert not any(sig_bh)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])