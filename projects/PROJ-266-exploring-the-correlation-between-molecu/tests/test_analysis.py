"""
Unit tests for correlation and FDR logic in code/data/analysis.py.

This module tests the statistical functions implemented in the analysis module:
- compute_correlations: Pearson and Spearman correlation calculation
- apply_benjamini_hochberg: FDR correction for multiple hypothesis testing
"""
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.analysis import compute_correlations, apply_benjamini_hochberg


class TestComputeCorrelations(unittest.TestCase):
    """Tests for the compute_correlations function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a simple synthetic dataset for testing
        np.random.seed(42)
        n_samples = 100
        
        # Generate correlated data
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.random.normal(0, 1, n_samples)
        x3 = x1 * 0.7 + np.random.normal(0, 0.3, n_samples)  # Correlated with x1
        
        # Create a DataFrame with flexibility descriptors and logPapp
        self.df = pd.DataFrame({
            'bond_variance': x1,
            'angle_variance': x2,
            'dihedral_variance': x3,
            'logPapp': x1 * 0.5 + x2 * 0.3 + np.random.normal(0, 0.2, n_samples)
        })

    def test_compute_correlations_returns_dict(self):
        """Test that compute_correlations returns a dictionary."""
        results = compute_correlations(self.df, 'logPapp')
        self.assertIsInstance(results, dict)

    def test_compute_correlations_includes_all_descriptors(self):
        """Test that all three descriptors are included in results."""
        results = compute_correlations(self.df, 'logPapp')
        
        self.assertIn('bond_variance', results)
        self.assertIn('angle_variance', results)
        self.assertIn('dihedral_variance', results)

    def test_compute_correlations_structure(self):
        """Test that each descriptor result has the correct structure."""
        results = compute_correlations(self.df, 'logPapp')
        
        for descriptor in ['bond_variance', 'angle_variance', 'dihedral_variance']:
            self.assertIn(descriptor, results)
            result = results[descriptor]
            
            self.assertIn('pearson', result)
            self.assertIn('pearson_pvalue', result)
            self.assertIn('spearman', result)
            self.assertIn('spearman_pvalue', result)
            
            # Check that values are floats
            self.assertIsInstance(result['pearson'], float)
            self.assertIsInstance(result['pearson_pvalue'], float)
            self.assertIsInstance(result['spearman'], float)
            self.assertIsInstance(result['spearman_pvalue'], float)

    def test_compute_correlations_positive_correlation(self):
        """Test that positively correlated variables yield positive coefficients."""
        results = compute_correlations(self.df, 'logPapp')
        
        # bond_variance and logPapp are positively correlated by design
        self.assertGreater(results['bond_variance']['pearson'], 0)
        self.assertGreater(results['bond_variance']['spearman'], 0)

    def test_compute_correlations_with_nan(self):
        """Test that compute_correlations handles NaN values correctly."""
        df_with_nan = self.df.copy()
        df_with_nan.loc[0, 'bond_variance'] = np.nan
        
        results = compute_correlations(df_with_nan, 'logPapp')
        
        # Should still return valid results (NaN rows are dropped)
        self.assertIn('bond_variance', results)
        self.assertIsInstance(results['bond_variance']['pearson'], float)

    def test_compute_correlations_perfect_correlation(self):
        """Test with perfectly correlated variables."""
        df_perfect = pd.DataFrame({
            'variance': np.arange(100),
            'target': np.arange(100)
        })
        
        results = compute_correlations(df_perfect, 'target')
        
        # Perfect correlation should yield coefficient of 1.0
        self.assertAlmostEqual(results['variance']['pearson'], 1.0, places=5)
        self.assertAlmostEqual(results['variance']['spearman'], 1.0, places=5)


class TestBenjaminiHochberg(unittest.TestCase):
    """Tests for the apply_benjamini_hochberg function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test p-values
        self.p_values = np.array([0.01, 0.03, 0.04, 0.06, 0.10, 0.20, 0.30, 0.40])
        self.descriptors = ['bond', 'angle', 'dihedral', 'rotatable', 'ring', 
                          'polar', 'hydrophobic', 'size']

    def test_apply_benjamini_hochberg_returns_dict(self):
        """Test that apply_benjamini_hochberg returns a dictionary."""
        results = apply_benjamini_hochberg(self.p_values, self.descriptors, alpha=0.05)
        self.assertIsInstance(results, dict)

    def test_apply_benjamini_hochberg_includes_all_descriptors(self):
        """Test that all descriptors are included in results."""
        results = apply_benjamini_hochberg(self.p_values, self.descriptors, alpha=0.05)
        
        for descriptor in self.descriptors:
            self.assertIn(descriptor, results)

    def test_apply_benjamini_hochberg_structure(self):
        """Test that each descriptor result has the correct structure."""
        results = apply_benjamini_hochberg(self.p_values, self.descriptors, alpha=0.05)
        
        for descriptor in self.descriptors:
            self.assertIn(descriptor, results)
            result = results[descriptor]
            
            self.assertIn('raw_pvalue', result)
            self.assertIn('adjusted_pvalue', result)
            self.assertIn('is_significant', result)
            
            # Check that values are floats or booleans
            self.assertIsInstance(result['raw_pvalue'], float)
            self.assertIsInstance(result['adjusted_pvalue'], float)
            self.assertIsInstance(result['is_significant'], bool)

    def test_apply_benjamini_hochberg_monotonicity(self):
        """Test that adjusted p-values are monotonically increasing."""
        results = apply_benjamini_hochberg(self.p_values, self.descriptors, alpha=0.05)
        
        # Sort by raw p-value
        sorted_results = sorted(results.items(), key=lambda x: x[1]['raw_pvalue'])
        
        adjusted_pvalues = [r[1]['adjusted_pvalue'] for r in sorted_results]
        
        # Check monotonicity
        for i in range(1, len(adjusted_pvalues)):
            self.assertGreaterEqual(adjusted_pvalues[i], adjusted_pvalues[i-1])

    def test_apply_benjamini_hochberg_significance_threshold(self):
        """Test that significance is correctly determined based on alpha."""
        # Create p-values where we know the expected significance
        p_values = np.array([0.001, 0.01, 0.05, 0.1, 0.2])
        descriptors = ['a', 'b', 'c', 'd', 'e']
        
        results = apply_benjamini_hochberg(p_values, descriptors, alpha=0.05)
        
        # At least the smallest p-value should be significant
        self.assertTrue(results['a']['is_significant'])
        
        # Larger p-values may or may not be significant depending on FDR correction
        # but the function should not crash

    def test_apply_benjamini_hochberg_with_all_significant(self):
        """Test with all p-values being very small."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        descriptors = ['a', 'b', 'c', 'd', 'e']
        
        results = apply_benjamini_hochberg(p_values, descriptors, alpha=0.05)
        
        # All should be significant
        for descriptor in descriptors:
            self.assertTrue(results[descriptor]['is_significant'])

    def test_apply_benjamini_hochberg_with_no_significant(self):
        """Test with all p-values being very large."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        descriptors = ['a', 'b', 'c', 'd', 'e']
        
        results = apply_benjamini_hochberg(p_values, descriptors, alpha=0.05)
        
        # None should be significant
        for descriptor in descriptors:
            self.assertFalse(results[descriptor]['is_significant'])

    def test_apply_benjamini_hochberg_adjusted_pvalue_bounds(self):
        """Test that adjusted p-values are within [0, 1]."""
        results = apply_benjamini_hochberg(self.p_values, self.descriptors, alpha=0.05)
        
        for descriptor in self.descriptors:
            adj_p = results[descriptor]['adjusted_pvalue']
            self.assertGreaterEqual(adj_p, 0.0)
            self.assertLessEqual(adj_p, 1.0)


class TestIntegration(unittest.TestCase):
    """Integration tests combining correlation and FDR functions."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)
        n_samples = 200
        
        # Create a dataset with known correlations
        x1 = np.random.normal(0, 1, n_samples)
        x2 = np.random.normal(0, 1, n_samples)
        x3 = x1 * 0.8 + np.random.normal(0, 0.2, n_samples)  # Strongly correlated
        
        self.df = pd.DataFrame({
            'bond_variance': x1,
            'angle_variance': x2,
            'dihedral_variance': x3,
            'logPapp': x1 * 0.6 + x3 * 0.3 + np.random.normal(0, 0.1, n_samples)
        })

    def test_full_pipeline(self):
        """Test the full pipeline from correlation to FDR correction."""
        # Compute correlations
        corr_results = compute_correlations(self.df, 'logPapp')
        
        # Extract p-values for FDR correction
        p_values = np.array([corr_results[desc]['pearson_pvalue'] 
                           for desc in ['bond_variance', 'angle_variance', 'dihedral_variance']])
        descriptors = ['bond_variance', 'angle_variance', 'dihedral_variance']
        
        # Apply FDR correction
        fdr_results = apply_benjamini_hochberg(p_values, descriptors, alpha=0.05)
        
        # Verify the pipeline completed successfully
        self.assertEqual(len(fdr_results), 3)
        
        # Check that at least one descriptor is significant (by design, bond and dihedral should be)
        significant_count = sum(1 for desc in descriptors if fdr_results[desc]['is_significant'])
        self.assertGreater(significant_count, 0)

    def test_end_to_end_reproducibility(self):
        """Test that running the pipeline twice gives the same results."""
        # First run
        corr_results_1 = compute_correlations(self.df, 'logPapp')
        p_values_1 = np.array([corr_results_1[desc]['pearson_pvalue'] 
                             for desc in ['bond_variance', 'angle_variance', 'dihedral_variance']])
        fdr_results_1 = apply_benjamini_hochberg(p_values_1, ['bond_variance', 'angle_variance', 'dihedral_variance'], alpha=0.05)
        
        # Second run
        corr_results_2 = compute_correlations(self.df, 'logPapp')
        p_values_2 = np.array([corr_results_2[desc]['pearson_pvalue'] 
                             for desc in ['bond_variance', 'angle_variance', 'dihedral_variance']])
        fdr_results_2 = apply_benjamini_hochberg(p_values_2, ['bond_variance', 'angle_variance', 'dihedral_variance'], alpha=0.05)
        
        # Results should be identical
        for desc in ['bond_variance', 'angle_variance', 'dihedral_variance']:
            self.assertAlmostEqual(corr_results_1[desc]['pearson'], corr_results_2[desc]['pearson'])
            self.assertAlmostEqual(fdr_results_1[desc]['adjusted_pvalue'], fdr_results_2[desc]['adjusted_pvalue'])
            self.assertEqual(fdr_results_1[desc]['is_significant'], fdr_results_2[desc]['is_significant'])


if __name__ == '__main__':
    unittest.main()