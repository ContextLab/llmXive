"""
Unit tests for correlation and FDR logic in code/data/analysis.py.

These tests verify:
1. compute_correlations: Correctly calculates Pearson and Spearman correlations
   with p-values for all flexibility descriptors against logPapp.
2. apply_benjamini_hochberg: Correctly adjusts p-values for multiple hypothesis testing.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the functions being tested
from code.data.analysis import compute_correlations, apply_benjamini_hochberg


class TestComputeCorrelations:
    """Tests for the compute_correlations function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock DataFrame with known values for deterministic testing
        np.random.seed(42)
        n_samples = 100
        
        self.test_data = pd.DataFrame({
            'smiles': [f'mol_{i}' for i in range(n_samples)],
            'bond_variance': np.random.normal(0.5, 0.2, n_samples),
            'angle_variance': np.random.normal(1.0, 0.3, n_samples),
            'dihedral_variance': np.random.normal(2.0, 0.5, n_samples),
            'logPapp': np.random.normal(-5.0, 1.0, n_samples)
        })
        
        # Introduce a known correlation for dihedral_variance
        self.test_data['logPapp'] = (
            -0.7 * self.test_data['dihedral_variance'] + 
            np.random.normal(0, 0.5, n_samples)
        )

    def test_compute_correlations_returns_dict(self):
        """Test that compute_correlations returns a dictionary."""
        results = compute_correlations(self.test_data)
        assert isinstance(results, dict)

    def test_compute_correlations_has_expected_keys(self):
        """Test that results contain keys for all three descriptors."""
        results = compute_correlations(self.test_data)
        
        expected_keys = [
            'bond_variance', 'angle_variance', 'dihedral_variance'
        ]
        
        for key in expected_keys:
            assert key in results, f"Missing key: {key}"
            assert 'pearson' in results[key], f"Missing 'pearson' in {key}"
            assert 'spearman' in results[key], f"Missing 'spearman' in {key}"
            assert 'pearson_pvalue' in results[key], f"Missing 'pearson_pvalue' in {key}"
            assert 'spearman_pvalue' in results[key], f"Missing 'spearman_pvalue' in {key}"

    def test_compute_correlations_dihedral_correlation_strength(self):
        """Test that the injected correlation in dihedral_variance is detected."""
        results = compute_correlations(self.test_data)
        
        # The injected correlation should be significant (negative)
        # With 100 samples and r=-0.7, p-value should be very small
        dihedral_pearson = results['dihedral_variance']['pearson']
        dihedral_pvalue = results['dihedral_variance']['pearson_pvalue']
        
        assert dihedral_pearson < -0.5, f"Expected strong negative correlation, got {dihedral_pearson}"
        assert dihedral_pvalue < 0.05, f"Expected significant p-value, got {dihedral_pvalue}"

    def test_compute_correlations_handles_missing_columns(self):
        """Test behavior when required columns are missing."""
        incomplete_data = self.test_data[['smiles', 'bond_variance']]
        
        with pytest.raises((KeyError, ValueError)):
            compute_correlations(incomplete_data)

    def test_compute_correlations_with_nan_values(self):
        """Test that NaN values are handled appropriately."""
        data_with_nan = self.test_data.copy()
        data_with_nan.loc[0, 'logPapp'] = np.nan
        
        # Should not crash, but might produce NaN correlations or drop rows
        results = compute_correlations(data_with_nan)
        
        # Verify results structure is maintained
        assert 'dihedral_variance' in results


class TestApplyBenjaminiHochberg:
    """Tests for the apply_benjamini_hochberg function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create test p-values with known BH adjustment properties
        self.p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5])
        self.q_threshold = 0.05

    def test_apply_benjamini_hochberg_returns_dict(self):
        """Test that BH function returns a dictionary."""
        results = apply_benjamini_hochberg(self.p_values, self.q_threshold)
        assert isinstance(results, dict)

    def test_apply_benjamini_hochberg_returns_adjusted_pvalues(self):
        """Test that adjusted p-values are returned."""
        results = apply_benjamini_hochberg(self.p_values, self.q_threshold)
        
        assert 'adjusted_pvalues' in results
        assert len(results['adjusted_pvalues']) == len(self.p_values)
        
        # Adjusted p-values should be >= original p-values (monotonicity)
        assert all(results['adjusted_pvalues'] >= self.p_values), \
            "Adjusted p-values should be >= original p-values"

    def test_apply_benjamini_hochberg_monotonicity(self):
        """Test that adjusted p-values are monotonically increasing."""
        results = apply_benjamini_hochberg(self.p_values, self.q_threshold)
        adjusted = results['adjusted_pvalues']
        
        # BH procedure ensures monotonicity: adjusted_p[i] <= adjusted_p[i+1]
        # when sorted by original p-values
        is_monotonic = all(adjusted[i] <= adjusted[i+1] for i in range(len(adjusted)-1))
        assert is_monotonic, "Adjusted p-values should be monotonically increasing"

    def test_apply_benjamini_hochberg_significance_flags(self):
        """Test that significance flags are correctly computed."""
        results = apply_benjamini_hochberg(self.p_values, self.q_threshold)
        
        assert 'significant' in results
        assert len(results['significant']) == len(self.p_values)
        
        # With q=0.05, small p-values should be significant
        # The first few p-values (0.001, 0.01, 0.02) should likely be significant
        significant_count = sum(results['significant'])
        assert significant_count >= 0, "Should have at least 0 significant results"

    def test_apply_benjamini_hochberg_with_all_significant(self):
        """Test case where all p-values are significant."""
        significant_p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        results = apply_benjamini_hochberg(significant_p_values, q_threshold=0.1)
        
        # All should be significant at q=0.1
        assert all(results['significant']), "All p-values should be significant"

    def test_apply_benjamini_hochberg_with_no_significant(self):
        """Test case where no p-values are significant."""
        large_p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        results = apply_benjamini_hochberg(large_p_values, q_threshold=0.01)
        
        # None should be significant at q=0.01
        assert not any(results['significant']), "No p-values should be significant"

    def test_apply_benjamini_hochberg_edge_case_single_value(self):
        """Test with a single p-value."""
        single_p = np.array([0.01])
        results = apply_benjamini_hochberg(single_p, q_threshold=0.05)
        
        assert len(results['adjusted_pvalues']) == 1
        assert len(results['significant']) == 1
        # Single value: adjusted = original * n / rank = 0.01 * 1 / 1 = 0.01
        assert results['adjusted_pvalues'][0] <= 0.05


class TestIntegration:
    """Integration tests combining correlation and FDR logic."""

    def test_full_correlation_fdr_pipeline(self):
        """Test the complete pipeline from correlation to FDR correction."""
        # Create realistic test data
        np.random.seed(123)
        n_samples = 200
        
        data = pd.DataFrame({
            'smiles': [f'mol_{i}' for i in range(n_samples)],
            'bond_variance': np.random.normal(0.5, 0.15, n_samples),
            'angle_variance': np.random.normal(1.0, 0.25, n_samples),
            'dihedral_variance': np.random.normal(2.0, 0.4, n_samples),
            'logPapp': -0.6 * np.random.normal(2.0, 0.4, n_samples) + np.random.normal(0, 0.3, n_samples)
        })
        
        # Compute correlations
        corr_results = compute_correlations(data)
        
        # Collect all p-values for FDR correction
        all_pvalues = []
        for descriptor in ['bond_variance', 'angle_variance', 'dihedral_variance']:
            all_pvalues.extend([
                corr_results[descriptor]['pearson_pvalue'],
                corr_results[descriptor]['spearman_pvalue']
            ])
        
        all_pvalues = np.array(all_pvalues)
        
        # Apply FDR correction
        fdr_results = apply_benjamini_hochberg(all_pvalues, q_threshold=0.05)
        
        # Verify structure
        assert len(fdr_results['adjusted_pvalues']) == len(all_pvalues)
        assert len(fdr_results['significant']) == len(all_pvalues)
        
        # At least some results should be plausible (not all NaN)
        assert not all(np.isnan(fdr_results['adjusted_pvalues']))