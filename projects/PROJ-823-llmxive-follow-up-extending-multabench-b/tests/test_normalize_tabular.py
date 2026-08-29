"""
Unit tests for T024f: Normalize Tabular Features
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.feature_engineering import normalize_features

class TestNormalizeFeatures(unittest.TestCase):

    def test_zscore_normalization(self):
        """Test z-score normalization produces mean ~0 and std ~1."""
        data = {
            'feature_a': [10.0, 20.0, 30.0, 40.0, 50.0],
            'feature_b': [5.0, 5.0, 5.0, 5.0, 5.0] # Zero variance
        }
        df = pd.DataFrame(data)
        
        normalized_df, metadata = normalize_features(df, method="zscore")
        
        # Check feature_a
        self.assertAlmostEqual(normalized_df['feature_a'].mean(), 0.0, places=5)
        self.assertAlmostEqual(normalized_df['feature_a'].std(), 1.0, places=5)
        
        # Check feature_b (zero variance handled)
        self.assertEqual(normalized_df['feature_b'].iloc[0], 0.0) # (5-5)/1 = 0
        
        # Check metadata
        self.assertIn('mean', metadata['feature_a'])
        self.assertIn('std', metadata['feature_a'])
        self.assertEqual(metadata['feature_a']['method'], 'zscore')

    def test_minmax_normalization(self):
        """Test min-max normalization produces range [0, 1]."""
        data = {
            'feature_a': [10.0, 20.0, 30.0, 40.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        normalized_df, metadata = normalize_features(df, method="minmax")
        
        self.assertAlmostEqual(normalized_df['feature_a'].min(), 0.0, places=5)
        self.assertAlmostEqual(normalized_df['feature_a'].max(), 1.0, places=5)

    def test_missing_value_imputation(self):
        """Test that missing values are imputed with the mean."""
        data = {
            'feature_a': [10.0, np.nan, 30.0, 40.0, 50.0]
        }
        df = pd.DataFrame(data)
        expected_mean = (10 + 30 + 40 + 50) / 4 # 32.5
        
        normalized_df, metadata = normalize_features(df, method="zscore")
        
        # The NaN should be filled with mean (32.5) before normalization
        # So the normalized value for the filled spot should be (32.5 - 32.5) / std = 0
        # But since we fill it, the row is no longer NaN.
        self.assertFalse(normalized_df['feature_a'].isna().any())
        
        # Verify the imputed value logic:
        # Original: [10, 32.5, 30, 40, 50] -> Mean = 32.5
        # Normalized: [(10-32.5)/std, 0, ...]
        # We just check it's not NaN and the mean is approx 0
        self.assertAlmostEqual(normalized_df['feature_a'].mean(), 0.0, places=5)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        normalized_df, metadata = normalize_features(df)
        self.assertTrue(normalized_df.empty)

    def test_no_numeric_columns(self):
        """Test handling of DataFrame with no numeric columns."""
        data = {
            'text_col': ['a', 'b', 'c']
        }
        df = pd.DataFrame(data)
        normalized_df, metadata = normalize_features(df)
        self.assertEqual(len(normalized_df), 3)
        self.assertEqual(len(metadata), 0)

if __name__ == '__main__':
    unittest.main()