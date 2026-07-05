"""
Unit tests for Benjamini-Hochberg FDR correction implementation.

This test suite verifies that the FDR correction logic in code/analysis/model.py
satisfies the Plan requirements:
- Correctly applies Benjamini-Hochberg procedure
- Handles edge cases (all p-values significant, none significant)
- Maintains monotonicity of adjusted p-values
- Works with hierarchical data structures
"""

import pytest
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

# Import the function to test
from analysis.model import calculate_fdr_adjusted_pvalues


class TestBenjaminiHochbergFDR:
    """Test suite for Benjamini-Hochberg FDR correction."""

    def test_basic_fdr_correction(self):
        """Test basic FDR correction with known p-values."""
        # Known p-values
        p_values = np.array([0.01, 0.04, 0.03, 0.001, 0.02, 0.10, 0.05])
        
        # Expected results using statsmodels as reference
        _, expected_rejected, expected_adjusted, _ = multipletests(
            p_values, alpha=0.05, method='fdr_bh'
        )
        
        # Run our implementation
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # Verify adjusted p-values match (within floating point tolerance)
        np.testing.assert_array_almost_equal(adjusted_pvalues, expected_adjusted, decimal=10)
        
        # Verify rejection decisions match
        np.testing.assert_array_equal(rejected, expected_rejected)

    def test_monotonicity_preservation(self):
        """Test that adjusted p-values maintain monotonicity."""
        # Unsorted p-values
        p_values = np.array([0.05, 0.01, 0.10, 0.03, 0.08])
        
        adjusted_pvalues, _ = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # After BH correction, adjusted p-values should be monotonically non-decreasing
        # when sorted by original p-value rank
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = adjusted_pvalues[sorted_indices]
        
        # Check monotonicity: each value should be >= previous
        assert np.all(np.diff(sorted_adjusted) >= -1e-10), \
            "Adjusted p-values should be monotonically non-decreasing"

    def test_all_significant_case(self):
        """Test when all p-values are very small."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # All should be rejected
        assert np.all(rejected), "All small p-values should be rejected"
        
        # Adjusted p-values should still be <= alpha for all
        assert np.all(adjusted_pvalues <= 0.05), \
            "All adjusted p-values should be <= alpha when all are significant"

    def test_none_significant_case(self):
        """Test when all p-values are large."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # None should be rejected
        assert not np.any(rejected), "No large p-values should be rejected"
        
        # All adjusted p-values should be > alpha
        assert np.all(adjusted_pvalues > 0.05), \
            "All adjusted p-values should be > alpha when none are significant"

    def test_edge_case_single_pvalue(self):
        """Test with a single p-value."""
        p_values = np.array([0.03])
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # For single p-value, adjusted should equal original
        np.testing.assert_almost_equal(adjusted_pvalues[0], p_values[0])
        assert rejected[0] == (p_values[0] < 0.05)

    def test_edge_case_zero_pvalue(self):
        """Test with p-value of exactly 0."""
        p_values = np.array([0.0, 0.05, 0.10])
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # Zero p-value should remain zero after adjustment
        assert adjusted_pvalues[0] == 0.0, "Zero p-value should remain zero"
        assert rejected[0], "Zero p-value should be rejected"

    def test_hierarchical_data_structure(self):
        """Test with DataFrame input simulating hierarchical model results."""
        # Create a DataFrame similar to what mixed-effects model would produce
        df = pd.DataFrame({
            'term': ['CSA_Index', 'Digital_Access', 'Finance_Access', 
                    'CSA_Index:Digital', 'CSA_Index:Finance', 'Control1', 'Control2'],
            'pvalue': [0.001, 0.04, 0.06, 0.03, 0.02, 0.15, 0.20],
            'estimate': [0.5, 0.3, 0.2, 0.1, 0.15, 0.05, 0.08]
        })
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(
            df['pvalue'].values, alpha=0.05
        )
        
        # Add results to DataFrame
        df['pvalue_adjusted'] = adjusted_pvalues
        df['rejected'] = rejected
        
        # Verify we have the same number of rows
        assert len(df) == 7
        
        # Verify at least some hypotheses are rejected
        assert df['rejected'].sum() > 0, "At least some hypotheses should be rejected"
        
        # Verify the CSA_Index (smallest p-value) is rejected
        assert df.loc[df['term'] == 'CSA_Index', 'rejected'].values[0], \
            "CSA_Index should be rejected (smallest p-value)"

    def test_alpha_parameter_variety(self):
        """Test with different alpha thresholds."""
        p_values = np.array([0.01, 0.04, 0.06, 0.10])
        
        for alpha in [0.01, 0.05, 0.10]:
            adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=alpha)
            
            # Verify adjusted p-values are correctly computed
            _, expected_rejected, expected_adjusted, _ = multipletests(
                p_values, alpha=alpha, method='fdr_bh'
            )
            
            np.testing.assert_array_almost_equal(adjusted_pvalues, expected_adjusted, decimal=10)
            np.testing.assert_array_equal(rejected, expected_rejected)

    def test_plan_requirement_fdr_not_bonferroni(self):
        """Verify we're using FDR, not Bonferroni, as per Plan requirements."""
        p_values = np.array([0.01, 0.04, 0.06, 0.10, 0.15])
        
        # Get our FDR results
        fdr_adjusted, _ = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # Get Bonferroni results for comparison
        _, _, bonf_adjusted, _ = multipletests(p_values, alpha=0.05, method='bonferroni')
        
        # FDR adjusted p-values should be less conservative (smaller) than Bonferroni
        assert np.all(fdr_adjusted <= bonf_adjusted), \
            "FDR adjusted p-values should be <= Bonferroni (less conservative)"
        
        # They should not be identical (unless all p-values are extreme)
        assert not np.allclose(fdr_adjusted, bonf_adjusted), \
            "FDR and Bonferroni should produce different results for typical data"

    def test_large_scale_hypothesis_testing(self):
        """Test with a larger number of hypotheses (simulating many predictors)."""
        np.random.seed(42)
        n_hypotheses = 100
        p_values = np.random.uniform(0, 1, n_hypotheses)
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # Verify output dimensions
        assert len(adjusted_pvalues) == n_hypotheses
        assert len(rejected) == n_hypotheses
        
        # Verify no NaN values
        assert not np.any(np.isnan(adjusted_pvalues)), "No NaN values in adjusted p-values"
        
        # Verify all adjusted p-values are in [0, 1]
        assert np.all((adjusted_pvalues >= 0) & (adjusted_pvalues <= 1)), \
            "All adjusted p-values should be in [0, 1]"

    def test_rejection_count_reasonableness(self):
        """Test that rejection count is reasonable for mixed p-value distribution."""
        # Create a mix of significant and non-significant p-values
        p_values = np.concatenate([
            np.random.uniform(0, 0.05, 20),  # Significant
            np.random.uniform(0.05, 1.0, 80)  # Non-significant
        ])
        
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # We should reject some, but not all
        n_rejected = np.sum(rejected)
        assert n_rejected > 0, "Should reject at least some hypotheses"
        assert n_rejected < len(p_values), "Should not reject all hypotheses"
        
        # The number rejected should be roughly proportional to the number of true signals
        # (with some variance due to randomness)
        assert 10 <= n_rejected <= 40, \
            f"Expected 10-40 rejections, got {n_rejected} (out of 100 with 20 true signals)"

    def test_input_validation(self):
        """Test that invalid inputs are handled gracefully."""
        # Empty array
        with pytest.raises((ValueError, IndexError)):
            calculate_fdr_adjusted_pvalues(np.array([]), alpha=0.05)
        
        # Negative p-values
        with pytest.raises(ValueError):
            calculate_fdr_adjusted_pvalues(np.array([-0.1, 0.5]), alpha=0.05)
        
        # P-values > 1
        with pytest.raises(ValueError):
            calculate_pvalues(np.array([0.5, 1.5]), alpha=0.05)

    def test_deterministic_results(self):
        """Test that results are deterministic for same input."""
        p_values = np.array([0.01, 0.04, 0.03, 0.001, 0.02])
        
        # Run twice
        adj1, rej1 = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        adj2, rej2 = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        
        # Results should be identical
        np.testing.assert_array_equal(adj1, adj2)
        np.testing.assert_array_equal(rej1, rej2)

    def test_integration_with_model_output_format(self):
        """Test that the function works with typical model output formats."""
        # Simulate a results DataFrame from statsmodels mixed-effects
        np.random.seed(123)
        n_terms = 15
        
        results_df = pd.DataFrame({
            'term': [f'term_{i}' for i in range(n_terms)],
            'coef': np.random.randn(n_terms),
            'std err': np.abs(np.random.randn(n_terms) * 0.1),
            'pvalue': np.random.uniform(0, 1, n_terms)
        })
        
        # Apply FDR correction
        adjusted_pvalues, rejected = calculate_fdr_adjusted_pvalues(
            results_df['pvalue'].values, alpha=0.05
        )
        
        # Add to DataFrame
        results_df['pvalue_fdr'] = adjusted_pvalues
        results_df['significant_fdr'] = rejected
        
        # Verify the DataFrame is intact
        assert len(results_df) == n_terms
        assert 'pvalue_fdr' in results_df.columns
        assert 'significant_fdr' in results_df.columns
        
        # Verify that significant terms have adjusted p-value < 0.05
        sig_terms = results_df[results_df['significant_fdr']]
        if len(sig_terms) > 0:
            assert np.all(sig_terms['pvalue_fdr'] < 0.05), \
                "Significant terms should have adjusted p-value < 0.05"

    def test_comparison_with_bonferroni_power(self):
        """Demonstrate that FDR has more power than Bonferroni."""
        # Create a scenario where FDR should find more discoveries
        np.random.seed(456)
        n_total = 50
        n_true_signals = 10
        
        # Mix of true signals and noise
        p_values = np.concatenate([
            np.random.beta(1, 10, n_true_signals),  # True signals (small p-values)
            np.random.uniform(0, 1, n_total - n_true_signals)  # Noise
        ])
        
        # Apply both corrections
        fdr_adjusted, fdr_rejected = calculate_fdr_adjusted_pvalues(p_values, alpha=0.05)
        _, bonf_rejected, _, _ = multipletests(p_values, alpha=0.05, method='bonferroni')
        
        # FDR should reject at least as many as Bonferroni
        assert np.sum(fdr_rejected) >= np.sum(bonf_rejected), \
            "FDR should reject at least as many hypotheses as Bonferroni"
        
        # In this setup, FDR should typically reject more
        if np.sum(bonf_rejected) < n_true_signals:
            assert np.sum(fdr_rejected) > np.sum(bonf_rejected), \
                "FDR should have more power to detect true signals"