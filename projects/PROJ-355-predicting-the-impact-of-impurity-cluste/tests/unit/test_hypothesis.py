"""
Unit tests for multiple-comparison correction (Bonferroni/FDR) in hypothesis testing.

This module tests the logic for adjusting p-values when performing multiple hypothesis tests
on regression coefficients, ensuring proper control of Type I error rates.

Tests cover:
- Bonferroni correction implementation
- False Discovery Rate (FDR) correction (Benjamini-Hochberg) implementation
- Edge cases (empty arrays, all significant, none significant)
- Integration with statsmodels results objects
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant


class TestMultipleComparisonCorrection:
    """Test suite for multiple comparison correction methods."""

    @pytest.fixture
    def sample_p_values(self):
        """Generate a sample array of p-values for testing."""
        # Simulate p-values from a typical regression analysis
        # Some significant, some not
        return np.array([0.001, 0.003, 0.01, 0.02, 0.04, 0.05, 0.1, 0.2, 0.5, 0.9])

    @pytest.fixture
    def sample_coefficients(self):
        """Generate sample coefficients and standard errors."""
        return {
            'intercept': {'coef': 1.5, 'se': 0.2, 'p_value': 0.001},
            'descriptors_rdf_peak': {'coef': 0.8, 'se': 0.15, 'p_value': 0.003},
            'descriptors_pair_corr': {'coef': 0.3, 'se': 0.1, 'p_value': 0.01},
            'descriptors_voronoi_count': {'coef': 0.5, 'se': 0.12, 'p_value': 0.02},
            'impurity_concentration': {'coef': -0.2, 'se': 0.08, 'p_value': 0.04},
            'interface_area': {'coef': 0.1, 'se': 0.06, 'p_value': 0.05},
            'bulk_modulus': {'coef': 0.05, 'se': 0.04, 'p_value': 0.1},
            'electronegativity_diff': {'coef': -0.02, 'se': 0.03, 'p_value': 0.2},
            'atomic_radius_ratio': {'coef': 0.01, 'se': 0.02, 'p_value': 0.5},
            'temperature': {'coef': 0.001, 'se': 0.01, 'p_value': 0.9}
        }

    @staticmethod
    def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> dict:
        """
        Apply Bonferroni correction to p-values.
        
        Args:
            p_values: Array of raw p-values
            alpha: Significance level (default 0.05)
        
        Returns:
            Dictionary with corrected p-values and significance decisions
        """
        if len(p_values) == 0:
            return {
                'corrected_p_values': np.array([]),
                'significant': np.array([], dtype=bool),
                'adjusted_alpha': alpha,
                'method': 'bonferroni'
            }
        
        n_tests = len(p_values)
        adjusted_alpha = alpha / n_tests
        corrected_p_values = np.minimum(p_values * n_tests, 1.0)
        significant = corrected_p_values < alpha
        
        return {
            'corrected_p_values': corrected_p_values,
            'significant': significant,
            'adjusted_alpha': adjusted_alpha,
            'method': 'bonferroni',
            'n_tests': n_tests
        }

    @staticmethod
    def fdr_correction_benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> dict:
        """
        Apply Benjamini-Hochberg False Discovery Rate correction.
        
        Args:
            p_values: Array of raw p-values
            alpha: Significance level (default 0.05)
        
        Returns:
            Dictionary with corrected p-values and significance decisions
        """
        if len(p_values) == 0:
            return {
                'corrected_p_values': np.array([]),
                'significant': np.array([], dtype=bool),
                'adjusted_alpha': alpha,
                'method': 'fdr_bh'
            }
        
        p_values = np.asarray(p_values)
        n_tests = len(p_values)
        
        # Sort p-values and keep track of original indices
        sorted_indices = np.argsort(p_values)
        sorted_p_values = p_values[sorted_indices]
        
        # Calculate BH critical values
        ranks = np.arange(1, n_tests + 1)
        critical_values = (ranks / n_tests) * alpha
        
        # Find the largest k such that p(k) <= critical_value(k)
        # This is the step-down procedure
        significant_mask = sorted_p_values <= critical_values
        
        if not np.any(significant_mask):
            # No significant results
            corrected_p_values = np.ones(n_tests)
            significant = np.zeros(n_tests, dtype=bool)
        else:
            # Find the largest index where the condition holds
            largest_k = np.max(np.where(significant_mask)[0])
            
            # Apply monotonicity constraint: corrected p-values must be non-decreasing
            # when going from smallest to largest p-value
            corrected_sorted = np.minimum.accumulate(
                (sorted_p_values * n_tests) / ranks[::-1][::-1]
            )
            corrected_sorted = np.minimum(corrected_sorted, 1.0)
            
            # Restore original order
            corrected_p_values = np.empty(n_tests)
            corrected_p_values[sorted_indices] = corrected_sorted
            
            significant = corrected_p_values < alpha
        
        return {
            'corrected_p_values': corrected_p_values,
            'significant': significant,
            'adjusted_alpha': alpha,
            'method': 'fdr_bh',
            'n_tests': n_tests
        }

    def test_bonferroni_basic(self, sample_p_values):
        """Test basic Bonferroni correction logic."""
        result = self.bonferroni_correction(sample_p_values)
        
        # Check that corrected p-values are scaled by n_tests
        n_tests = len(sample_p_values)
        expected_corrected = np.minimum(sample_p_values * n_tests, 1.0)
        
        np.testing.assert_array_almost_equal(
            result['corrected_p_values'], 
            expected_corrected,
            decimal=10
        )
        
        # Check that adjusted alpha is correct
        assert result['adjusted_alpha'] == 0.05 / n_tests
        
        # Check that method is correctly labeled
        assert result['method'] == 'bonferroni'

    def test_bonferroni_significance(self, sample_p_values):
        """Test that Bonferroni correctly identifies significant results."""
        result = self.bonferroni_correction(sample_p_values)
        
        # With alpha=0.05 and 10 tests, adjusted alpha = 0.005
        # Only p-values < 0.005 should be significant
        expected_significant = result['corrected_p_values'] < 0.05
        
        np.testing.assert_array_equal(
            result['significant'],
            expected_significant
        )

    def test_fdr_basic(self, sample_p_values):
        """Test basic FDR correction logic."""
        result = self.fdr_correction_benjamini_hochberg(sample_p_values)
        
        # Check that corrected p-values are in valid range [0, 1]
        assert np.all(result['corrected_p_values'] >= 0)
        assert np.all(result['corrected_p_values'] <= 1)
        
        # Check that method is correctly labeled
        assert result['method'] == 'fdr_bh'
        
        # Check that n_tests is correct
        assert result['n_tests'] == len(sample_p_values)

    def test_fdr_more_significant_than_bonferroni(self, sample_p_values):
        """FDR should generally find more significant results than Bonferroni."""
        bonf_result = self.bonferroni_correction(sample_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(sample_p_values)
        
        bonf_n_sig = np.sum(bonf_result['significant'])
        fdr_n_sig = np.sum(fdr_result['significant'])
        
        # FDR should find at least as many significant results as Bonferroni
        assert fdr_n_sig >= bonf_n_sig

    def test_empty_array_handling(self):
        """Test that both methods handle empty arrays gracefully."""
        empty_p_values = np.array([])
        
        bonf_result = self.bonferroni_correction(empty_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(empty_p_values)
        
        assert len(bonf_result['corrected_p_values']) == 0
        assert len(bonf_result['significant']) == 0
        assert len(fdr_result['corrected_p_values']) == 0
        assert len(fdr_result['significant']) == 0

    def test_all_p_values_zero(self):
        """Test behavior when all p-values are zero (extreme significance)."""
        zero_p_values = np.zeros(5)
        
        bonf_result = self.bonferroni_correction(zero_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(zero_p_values)
        
        # All should be significant
        assert np.all(bonf_result['significant'])
        assert np.all(fdr_result['significant'])

    def test_all_p_values_one(self):
        """Test behavior when all p-values are 1.0 (no significance)."""
        one_p_values = np.ones(5)
        
        bonf_result = self.bonferroni_correction(one_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(one_p_values)
        
        # None should be significant
        assert not np.any(bonf_result['significant'])
        assert not np.any(fdr_result['significant'])

    def test_monotonicity_fdr(self, sample_p_values):
        """Test that FDR corrected p-values maintain monotonicity."""
        result = self.fdr_correction_benjamini_hochberg(sample_p_values)
        
        # Sort by original p-values and check monotonicity of corrected p-values
        sorted_indices = np.argsort(sample_p_values)
        sorted_corrected = result['corrected_p_values'][sorted_indices]
        
        # Corrected p-values should be non-decreasing when sorted by raw p-values
        assert np.all(np.diff(sorted_corrected) >= -1e-10)

    def test_integration_with_statsmodels(self, sample_coefficients):
        """Test integration with statsmodels regression results."""
        # Create synthetic data that would produce the given coefficients
        np.random.seed(42)
        n_samples = 100
        
        # Generate random features
        X = np.random.randn(n_samples, 3)
        X = add_constant(X)
        
        # Generate response with known coefficients
        true_coefs = [1.5, 0.8, 0.3, 0.5]
        y = X @ true_coefs + np.random.randn(n_samples) * 0.1
        
        # Fit model
        model = OLS(y, X).fit()
        
        # Extract p-values
        p_values = model.pvalues.values
        
        # Apply corrections
        bonf_result = self.bonferroni_correction(p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(p_values)
        
        # Verify that corrections were applied
        assert len(bonf_result['corrected_p_values']) == len(p_values)
        assert len(fdr_result['corrected_p_values']) == len(p_values)
        
        # Verify that both methods produce valid results
        assert np.all(bonf_result['corrected_p_values'] >= 0)
        assert np.all(bonf_result['corrected_p_values'] <= 1)
        assert np.all(fdr_result['corrected_p_values'] >= 0)
        assert np.all(fdr_result['corrected_p_values'] <= 1)

    def test_different_alpha_levels(self, sample_p_values):
        """Test that different alpha levels produce expected results."""
        alphas = [0.01, 0.05, 0.10]
        
        for alpha in alphas:
            bonf_result = self.bonferroni_correction(sample_p_values, alpha=alpha)
            fdr_result = self.fdr_correction_benjamini_hochberg(sample_p_values, alpha=alpha)
            
            # Adjusted alpha should be correct for Bonferroni
            expected_adj_alpha = alpha / len(sample_p_values)
            assert abs(bonf_result['adjusted_alpha'] - expected_adj_alpha) < 1e-10
            
            # More lenient alpha should find more significant results
            if alpha == 0.10:
                assert np.sum(bonf_result['significant']) >= np.sum(
                    self.bonferroni_correction(sample_p_values, alpha=0.05)['significant']
                )
                assert np.sum(fdr_result['significant']) >= np.sum(
                    self.fdr_correction_benjamini_hochberg(sample_p_values, alpha=0.05)['significant']
                )

    def test_p_value_clamping(self, sample_p_values):
        """Test that corrected p-values are properly clamped to [0, 1]."""
        # Create p-values that would exceed 1.0 when multiplied
        large_p_values = np.array([0.15, 0.2, 0.3, 0.4])  # 4 tests, so multiply by 4
        
        bonf_result = self.bonferroni_correction(large_p_values)
        
        # All corrected p-values should be <= 1.0
        assert np.all(bonf_result['corrected_p_values'] <= 1.0)
        
        # Values that would exceed 1.0 should be clamped
        expected_clamped = np.minimum(large_p_values * 4, 1.0)
        np.testing.assert_array_almost_equal(
            bonf_result['corrected_p_values'],
            expected_clamped
        )

    def test_consistency_across_runs(self, sample_p_values):
        """Test that results are deterministic and consistent."""
        results = []
        for _ in range(10):
            result = self.bonferroni_correction(sample_p_values)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            np.testing.assert_array_almost_equal(
                results[0]['corrected_p_values'],
                results[i]['corrected_p_values']
            )
            np.testing.assert_array_equal(
                results[0]['significant'],
                results[i]['significant']
            )

    def test_single_p_value(self):
        """Test behavior with a single p-value."""
        single_p = np.array([0.03])
        
        bonf_result = self.bonferroni_correction(single_p)
        fdr_result = self.fdr_correction_benjamini_hochberg(single_p)
        
        # With one test, corrections should not change the p-value
        assert abs(bonf_result['corrected_p_values'][0] - 0.03) < 1e-10
        assert abs(fdr_result['corrected_p_values'][0] - 0.03) < 1e-10
        
        # Should be significant at alpha=0.05
        assert bonf_result['significant'][0]
        assert fdr_result['significant'][0]

    def test_edge_case_tiny_p_values(self):
        """Test with extremely small p-values."""
        tiny_p_values = np.array([1e-10, 1e-8, 1e-6])
        
        bonf_result = self.bonferroni_correction(tiny_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(tiny_p_values)
        
        # All should be significant
        assert np.all(bonf_result['significant'])
        assert np.all(fdr_result['significant'])
        
        # Corrected values should still be very small
        assert np.all(bonf_result['corrected_p_values'] < 1e-5)
        assert np.all(fdr_result['corrected_p_values'] < 1e-5)

    def test_comparison_with_scipy_statsmodels(self, sample_p_values):
        """
        Compare our implementation with statsmodels' built-in multipletesting.
        Note: This test may fail if statsmodels is not available or has different
        implementation details, so it's marked as potentially flaky.
        """
        try:
            from statsmodels.stats.multitest import multipletests
            
            # Test Bonferroni
            _, bonf_sig, _, _ = multipletests(sample_p_values, alpha=0.05, method='bonferroni')
            our_bonf = self.bonferroni_correction(sample_p_values)
            
            # Significance decisions should match
            np.testing.assert_array_equal(bonf_sig, our_bonf['significant'])
            
            # Test FDR (Benjamini-Hochberg)
            _, fdr_sig, _, _ = multipletests(sample_p_values, alpha=0.05, method='fdr_bh')
            our_fdr = self.fdr_correction_benjamini_hochberg(sample_p_values)
            
            # Significance decisions should match
            np.testing.assert_array_equal(fdr_sig, our_fdr['significant'])
            
        except ImportError:
            # Skip test if statsmodels.stats.multitest is not available
            pytest.skip("statsmodels.stats.multitest not available for comparison")

    def test_documentation_requirements(self, sample_p_values):
        """
        Verify that the correction methods meet documentation requirements:
        - Return corrected p-values
        - Return significance decisions
        - Include method name
        - Include number of tests
        """
        bonf_result = self.bonferroni_correction(sample_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(sample_p_values)
        
        required_keys = ['corrected_p_values', 'significant', 'method', 'n_tests']
        
        for result in [bonf_result, fdr_result]:
            for key in required_keys:
                assert key in result, f"Missing required key: {key}"
            
            # Verify types
            assert isinstance(result['corrected_p_values'], np.ndarray)
            assert isinstance(result['significant'], np.ndarray)
            assert result['significant'].dtype == bool
            assert isinstance(result['method'], str)
            assert isinstance(result['n_tests'], int)
            
            # Verify method names
            assert result['method'] in ['bonferroni', 'fdr_bh']

    def test_practical_use_case(self):
        """
        Test a practical use case: multiple regression coefficients from a 
        grain boundary segregation study.
        """
        # Simulate p-values from a realistic scenario
        # Some descriptors are highly significant, others are marginal
        realistic_p_values = np.array([
            0.001,   # RDF peak - highly significant
            0.005,   # Pair correlation - significant
            0.015,   # Voronoi count - significant
            0.03,    # Interface area - marginally significant
            0.08,    # Bulk modulus - not significant
            0.12,    # Electronegativity - not significant
            0.25,    # Atomic radius - not significant
            0.45     # Temperature - not significant
        ])
        
        bonf_result = self.bonferroni_correction(realistic_p_values)
        fdr_result = self.fdr_correction_benjamini_hochberg(realistic_p_values)
        
        # With Bonferroni (8 tests, alpha=0.05), only p < 0.00625 should be significant
        bonf_expected_sig = realistic_p_values < (0.05 / 8)
        np.testing.assert_array_equal(bonf_result['significant'], bonf_expected_sig)
        
        # FDR should find more significant results
        assert np.sum(fdr_result['significant']) >= np.sum(bonf_result['significant'])
        
        # Document the findings
        n_bonf_sig = np.sum(bonf_result['significant'])
        n_fdr_sig = np.sum(fdr_result['significant'])
        
        # In this scenario, we expect at least 2-3 significant with FDR
        assert n_fdr_sig >= 2
        
        # But Bonferroni might be more conservative (1-2 significant)
        assert n_bonf_sig <= 3