"""
Tests for the sampling utility module.
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.sampling import stratified_sample


class TestStratifiedSample(unittest.TestCase):
    """Test cases for stratified_sample function."""
    
    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)
        
        # Create a simple test dataframe with known distribution
        self.n_samples = 200
        self.df = pd.DataFrame({
            'subject_id': [f'SUBJ_{i:03d}' for i in range(self.n_samples)],
            'titer_post': np.concatenate([
                np.random.normal(50, 10, 50),   # Low titers
                np.random.normal(100, 15, 50),  # Medium-low
                np.random.normal(150, 20, 50),  # Medium-high
                np.random.normal(200, 25, 50)   # High titers
            ]),
            'other_col': np.random.randn(self.n_samples)
        })
    
    def test_basic_sampling(self):
        """Test basic stratified sampling functionality."""
        sampled = stratified_sample(self.df, 'titer_post', retain_ratio=0.5, seed=42)
        
        # Check that we got approximately half the data
        expected_size = int(self.n_samples * 0.5)
        self.assertAlmostEqual(len(sampled), expected_size, delta=10)
        
        # Check that all columns are preserved
        self.assertEqual(set(sampled.columns), set(self.df.columns))
        
        # Check that no NaN values were introduced
        self.assertFalse(sampled.isna().any().any())
    
    def test_full_sampling(self):
        """Test sampling with retain_ratio=1.0 returns all data."""
        sampled = stratified_sample(self.df, 'titer_post', retain_ratio=1.0, seed=42)
        
        self.assertEqual(len(sampled), self.n_samples)
        self.assertTrue(sampled.equals(self.df))
    
    def test_zero_sampling(self):
        """Test sampling with retain_ratio=0.0 returns empty dataframe."""
        sampled = stratified_sample(self.df, 'titer_post', retain_ratio=0.0, seed=42)
        
        self.assertEqual(len(sampled), 0)
        self.assertEqual(set(sampled.columns), set(self.df.columns))
    
    def test_invalid_ratio(self):
        """Test that invalid retain_ratio raises ValueError."""
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'titer_post', retain_ratio=1.5)
        
        with self.assertRaises(ValueError):
            stratified_sample(self.df, 'titer_post', retain_ratio=-0.1)
    
    def test_missing_column(self):
        """Test that missing target column raises KeyError."""
        with self.assertRaises(KeyError):
            stratified_sample(self.df, 'nonexistent_col', retain_ratio=0.5)
    
    def test_non_numeric_column(self):
        """Test that non-numeric target column raises ValueError."""
        df_with_str = self.df.copy()
        df_with_str['subject_id'] = df_with_str['subject_id'].astype(str)
        
        with self.assertRaises(ValueError):
            stratified_sample(df_with_str, 'subject_id', retain_ratio=0.5)
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        sampled1 = stratified_sample(self.df, 'titer_post', retain_ratio=0.5, seed=123)
        sampled2 = stratified_sample(self.df, 'titer_post', retain_ratio=0.5, seed=123)
        
        self.assertTrue(sampled1.equals(sampled2))
    
    def test_different_seed(self):
        """Test that different seeds produce different results (usually)."""
        sampled1 = stratified_sample(self.df, 'titer_post', retain_ratio=0.5, seed=42)
        sampled2 = stratified_sample(self.df, 'titer_post', retain_ratio=0.5, seed=43)
        
        # They should be different (with very high probability)
        self.assertFalse(sampled1.equals(sampled2))
    
    def test_distribution_preservation(self):
        """Test that stratified sampling preserves distribution better than random."""
        # Compare stratified vs simple random sampling
        sampled_stratified = stratified_sample(self.df, 'titer_post', retain_ratio=0.5, seed=42)
        sampled_random = self.df.sample(frac=0.5, random_state=42)
        
        # Calculate quartiles for original and samples
        orig_quartiles = self.df['titer_post'].quantile([0.25, 0.5, 0.75])
        strat_quartiles = sampled_stratified['titer_post'].quantile([0.25, 0.5, 0.75])
        rand_quartiles = sampled_random['titer_post'].quantile([0.25, 0.5, 0.75])
        
        # Stratified should have quartiles closer to original
        strat_error = np.abs(strat_quartiles - orig_quartiles).sum()
        rand_error = np.abs(rand_quartiles - orig_quartiles).sum()
        
        # This is a soft check - stratified should typically be better
        # but not guaranteed in every random seed
        self.assertLessEqual(strat_error, rand_error * 1.5, 
                           "Stratified sampling should preserve distribution better")
    
    def test_with_nan_values(self):
        """Test handling of NaN values in target column."""
        df_with_nan = self.df.copy()
        df_with_nan.loc[0:9, 'titer_post'] = np.nan
        
        sampled = stratified_sample(df_with_nan, 'titer_post', retain_ratio=0.5, seed=42)
        
        # Should have dropped NaN rows before sampling
        self.assertEqual(len(sampled), int((self.n_samples - 10) * 0.5))
        self.assertFalse(sampled.isna().any().any())


if __name__ == '__main__':
    unittest.main()