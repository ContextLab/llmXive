"""
Tests for sampling utilities.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.sampling import stratified_sample, simple_random_sample


class TestSampling(unittest.TestCase):
    """Test cases for sampling utilities."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test DataFrame with known distribution
        np.random.seed(42)
        n_samples = 1000
        self.df = pd.DataFrame({
            'subject_id': [f'SUBJ_{i:03d}' for i in range(n_samples)],
            'target_col': np.random.normal(loc=50, scale=20, size=n_samples),
            'value1': np.random.rand(n_samples),
            'value2': np.random.rand(n_samples)
        })

    def test_stratified_sample_preserves_ratio(self):
        """Test that stratified sample retains approximately the correct ratio."""
        retain_ratio = 0.5
        sampled = stratified_sample(self.df, 'target_col', retain_ratio, seed=42)

        expected_rows = int(len(self.df) * retain_ratio)
        actual_rows = len(sampled)

        # Allow some tolerance due to rounding
        self.assertAlmostEqual(actual_rows, expected_rows, delta=10)

    def test_stratified_sample_preserves_distribution(self):
        """Test that stratified sample preserves the distribution of target column."""
        retain_ratio = 0.5
        sampled = stratified_sample(self.df, 'target_col', retain_ratio, seed=42)

        # Compare quartiles
        original_quartiles = self.df['target_col'].quantile([0.25, 0.5, 0.75])
        sampled_quartiles = sampled['target_col'].quantile([0.25, 0.5, 0.75])

        # Quartiles should be similar (within 10% tolerance)
        for orig_q, samp_q in zip(original_quartiles, sampled_quartiles):
            if orig_q != 0:
                relative_diff = abs(orig_q - samp_q) / abs(orig_q)
                self.assertLess(relative_diff, 0.15,
                              f"Quartile difference too large: {orig_q} vs {samp_q}")

    def test_stratified_sample_invalid_ratio(self):
        """Test that invalid retain_ratio raises ValueError."""
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'target_col', 1.5)

        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'target_col', -0.1)

    def test_stratified_sample_missing_column(self):
        """Test that missing target column raises ValueError."""
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'nonexistent_col', 0.5)

    def test_stratified_sample_non_numeric(self):
        """Test that non-numeric target column raises ValueError."""
        df_with_str = self.df.copy()
        df_with_str['str_col'] = ['str'] * len(df_with_str)

        with self.assertRaises(ValueError):
            stratified_sample(df_with_str, 'str_col', 0.5)

    def test_stratified_sample_empty_df(self):
        """Test that empty DataFrame returns empty DataFrame."""
        empty_df = pd.DataFrame(columns=['subject_id', 'target_col', 'value1'])
        sampled = stratified_sample(empty_df, 'target_col', 0.5)
        self.assertTrue(sampled.empty)

    def test_simple_random_sample(self):
        """Test simple random sampling functionality."""
        retain_ratio = 0.3
        sampled = simple_random_sample(self.df, retain_ratio, seed=42)

        expected_rows = int(len(self.df) * retain_ratio)
        self.assertAlmostEqual(len(sampled), expected_rows, delta=5)

    def test_deterministic_sampling(self):
        """Test that sampling is deterministic with fixed seed."""
        sampled1 = stratified_sample(self.df, 'target_col', 0.5, seed=123)
        sampled2 = stratified_sample(self.df, 'target_col', 0.5, seed=123)

        pd.testing.assert_frame_equal(sampled1, sampled2)


if __name__ == '__main__':
    unittest.main()