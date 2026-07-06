"""
Unit tests for code/correlate_bulk.py
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from correlate_bulk import compute_correlations, bonferroni_correction

class TestCorrelationFunctions(unittest.TestCase):

    def setUp(self):
        """Create a small synthetic dataset for testing."""
        np.random.seed(42)
        n = 50
        self.x = np.random.randn(n)
        self.y_linear = 2 * self.x + np.random.randn(n) * 0.5
        self.y_noisy = np.random.randn(n)
        self.df_linear = pd.DataFrame({'x': self.x, 'y': self.y_linear})
        self.df_noisy = pd.DataFrame({'x': self.x, 'y': self.y_noisy})

    def test_compute_correlations_strong_positive(self):
        """Test Pearson and Spearman on strongly correlated data."""
        result = compute_correlations(self.df_linear, 'x', 'y')
        
        self.assertGreater(result['pearson_r'], 0.8)
        self.assertGreater(result['spearman_r'], 0.8)
        self.assertLess(result['p_pearson'], 0.05)
        self.assertLess(result['p_spearman'], 0.05)
        
        # Check CI structure
        self.assertIsInstance(result['pearson_ci'], tuple)
        self.assertEqual(len(result['pearson_ci']), 2)
        self.assertTrue(result['pearson_ci'][0] < result['pearson_ci'][1])

    def test_compute_correlations_no_correlation(self):
        """Test on uncorrelated data."""
        result = compute_correlations(self.df_noisy, 'x', 'y')
        
        # Correlation should be near zero
        self.assertLess(abs(result['pearson_r']), 0.3)
        self.assertGreater(result['p_pearson'], 0.05)

    def test_compute_correlations_nan_handling(self):
        """Test handling of NaN values."""
        df_nan = self.df_linear.copy()
        df_nan.loc[0, 'y'] = np.nan
        
        result = compute_correlations(df_nan, 'x', 'y')
        
        # Should still compute on remaining data
        self.assertTrue(np.isfinite(result['pearson_r']))

    def test_compute_correlations_insufficient_data(self):
        """Test with too few data points."""
        df_small = pd.DataFrame({'x': [1.0, 2.0], 'y': [3.0, 4.0]})
        result = compute_correlations(df_small, 'x', 'y')
        
        # With 2 points, correlation is 1.0 or -1.0, but p-value might be NaN or 0.
        # The function should not crash.
        self.assertIn('pearson_r', result)

    def test_bonferroni_correction(self):
        """Test Bonferroni correction logic."""
        p_values = [0.01, 0.02, 0.05, 0.10]
        n_tests = 4
        
        adjusted = bonferroni_correction(p_values, n_tests)
        
        expected = [0.04, 0.08, 0.20, 0.40]
        
        for a, e in zip(adjusted, expected):
            self.assertAlmostEqual(a, e, places=5)
        
        # Check capping at 1.0
        p_high = [0.9, 0.95]
        adjusted_high = bonferroni_correction(p_high, 2)
        self.assertEqual(adjusted_high[1], 1.0)

if __name__ == '__main__':
    unittest.main()
