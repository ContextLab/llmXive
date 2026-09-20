"""
Unit tests for the sampling utility.
"""
import unittest
import pandas as pd
import numpy as np
from code.utils.sampling import stratified_sample


class TestStratifiedSampling(unittest.TestCase):
    
    def setUp(self):
        """Create a sample DataFrame for testing."""
        np.random.seed(42)
        n = 1000
        # Create a target column with a known distribution
        self.df = pd.DataFrame({
            'id': range(n),
            'target': np.random.normal(loc=100, scale=20, size=n),
            'value': np.random.rand(n)
        })

    def test_retain_ratio_full(self):
        """Test that retain_ratio=1.0 returns the full dataset."""
        result = stratified_sample(self.df, 'target', retain_ratio=1.0, seed=42)
        self.assertEqual(len(result), len(self.df))
        self.assertTrue(result.equals(self.df))

    def test_retain_ratio_half(self):
        """Test that retain_ratio=0.5 returns approximately half the data."""
        result = stratified_sample(self.df, 'target', retain_ratio=0.5, seed=42)
        expected_len = int(len(self.df) * 0.5)
        # Allow small variation due to rounding
        self.assertGreaterEqual(len(result), expected_len - 5)
        self.assertLessEqual(len(result), expected_len + 5)

    def test_retain_ratio_zero(self):
        """Test that retain_ratio=0.0 returns at least 1 row (min sample)."""
        result = stratified_sample(self.df, 'target', retain_ratio=0.0, seed=42)
        # The function ensures at least 1 sample per quartile, so min 4 rows
        self.assertGreater(len(result), 0)

    def test_invalid_target_col(self):
        """Test that an invalid target column raises ValueError."""
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'nonexistent_col', retain_ratio=0.5)

    def test_invalid_ratio(self):
        """Test that invalid retain_ratio raises ValueError."""
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'target', retain_ratio=1.5)
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'target', retain_ratio=-0.1)

    def test_distribution_preservation(self):
        """Test that the sample preserves the distribution of the target."""
        # Use a large sample to ensure statistical significance
        large_df = pd.DataFrame({
            'target': np.concatenate([np.ones(500), np.ones(500) * 2, np.ones(500) * 3]),
            'val': range(1500)
        })
        result = stratified_sample(large_df, 'target', retain_ratio=0.5, seed=42)
        
        # Check that we have representation from each distinct value
        unique_orig = set(large_df['target'].unique())
        unique_sample = set(result['target'].unique())
        self.assertEqual(unique_orig, unique_sample)
    
    def test_reproducibility(self):
        """Test that the same seed produces the same result."""
        result1 = stratified_sample(self.df, 'target', retain_ratio=0.5, seed=123)
        result2 = stratified_sample(self.df, 'target', retain_ratio=0.5, seed=123)
        self.assertTrue(result1.equals(result2))


if __name__ == '__main__':
    unittest.main()