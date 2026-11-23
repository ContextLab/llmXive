import unittest
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to import preprocess module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code', 'data')))

from preprocess import (
    load_gdelt_data,
    load_google_trends_data,
    align_timestamps,
    test_stationarity,
    ensure_stationarity,
    normalize_to_zscore,
    validate_data_length,
    save_to_csv
)

class TestPreprocessingPipelineT021(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory and mock data files."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, 'raw')
        self.processed_dir = os.path.join(self.temp_dir, 'processed')
        os.makedirs(self.raw_dir)
        os.makedirs(self.processed_dir)
        
        # Create mock GDELT data
        dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
        gdelt_data = {
            'date': dates,
            'event_count': np.random.randint(10, 100, size=len(dates)),
            'sentiment_score': np.random.uniform(-1, 1, size=len(dates))
        }
        self.gdelt_df = pd.DataFrame(gdelt_data)
        self.gdelt_path = os.path.join(self.raw_dir, 'gdelt_events.csv')
        self.gdelt_df.to_csv(self.gdelt_path, index=False)
        
        # Create mock Trends data (slightly different date range to test intersection)
        dates_trends = pd.date_range(start='2020-03-01', end='2021-03-01', freq='D')
        trends_data = {
            'date': dates_trends,
            'anticipatory_anxiety': np.random.randint(0, 100, size=len(dates_trends)),
            'worry_future': np.random.randint(0, 100, size=len(dates_trends))
        }
        self.trends_df = pd.DataFrame(trends_data)
        self.trends_path = os.path.join(self.raw_dir, 'google_trends.csv')
        self.trends_df.to_csv(self.trends_path, index=False)

    def test_timestamp_alignment_intersection(self):
        """Test that alignment correctly finds intersection and handles NaN."""
        # Load manually to bypass path logic in test
        gdelt_df = self.gdelt_df.copy()
        trends_df = self.trends_df.copy()
        
        # Ensure date is datetime
        gdelt_df['date'] = pd.to_datetime(gdelt_df['date'])
        trends_df['date'] = pd.to_datetime(trends_df['date'])
        
        aligned = align_timestamps(gdelt_df, trends_df)
        
        # Check intersection logic
        expected_start = pd.Timestamp('2020-03-01')
        expected_end = pd.Timestamp('2020-12-31')
        
        self.assertEqual(aligned.index.min(), expected_start)
        self.assertEqual(aligned.index.max(), expected_end)
        
        # Check that NaNs were interpolated (if any were introduced, though here we have full overlap in range)
        # To force NaNs, we could introduce a gap, but standard intersection preserves data.
        # The function handles interpolation if we had missing dates in the source.
        
    def test_adf_stationarity_detection(self):
        """Test ADF test on a known non-stationary series (random walk)."""
        # Create a random walk
        np.random.seed(42)
        walk = pd.Series(np.cumsum(np.random.randn(100)))
        
        is_stat, p_val = test_stationarity(walk, "random_walk")
        
        # Random walk should be non-stationary
        self.assertFalse(is_stat)
        self.assertGreaterEqual(p_val, 0.05)
        
    def test_ensure_stationarity_differencing(self):
        """Test that non-stationary series gets differenced."""
        # Create a random walk
        np.random.seed(42)
        walk = pd.Series(np.cumsum(np.random.randn(100)), name='random_walk')
        df = pd.DataFrame({'date': pd.date_range(start='2020-01-01', periods=100), 'walk': walk})
        df.set_index('date', inplace=True)
        
        processed_df, log_df = ensure_stationarity(df, ['walk'])
        
        # Check log
        self.assertEqual(len(log_df), 1)
        self.assertTrue(log_df.iloc[0]['differenced'])
        self.assertTrue(log_df.iloc[0]['is_stationary'])
        
    def test_normalize_to_zscore(self):
        """Test Z-score normalization."""
        data = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=50),
            'value': [10, 20, 30, 40, 50] * 10
        })
        data.set_index('date', inplace=True)
        
        normalized = normalize_to_zscore(data, ['value'])
        
        mean = normalized['value'].mean()
        std = normalized['value'].std()
        
        self.assertAlmostEqual(mean, 0.0, places=5)
        self.assertAlmostEqual(std, 1.0, places=5)
        
    def test_validate_data_length(self):
        """Test data length validation."""
        short_df = pd.DataFrame({'date': pd.date_range(start='2020-01-01', periods=10)})
        long_df = pd.DataFrame({'date': pd.date_range(start='2020-01-01', periods=50)})
        
        self.assertFalse(validate_data_length(short_df, min_length=20))
        self.assertTrue(validate_data_length(long_df, min_length=20))

    def test_full_pipeline_integration(self):
        """Test the full T021 pipeline: Load -> Align -> Stationarity -> Normalize -> Save."""
        # Mock the file paths in the module by patching or just using our temp files
        # Since the functions take optional paths, we pass them directly
        
        gdelt_df = load_gdelt_data(self.gdelt_path)
        trends_df = load_google_trends_data(self.trends_path)
        
        aligned = align_timestamps(gdelt_df, trends_df)
        
        # Validate length
        self.assertTrue(validate_data_length(aligned, min_length=20))
        
        # Identify numeric cols
        numeric_cols = aligned.select_dtypes(include=[np.number]).columns.tolist()
        
        # Stationarity
        stationary_df, _ = ensure_stationarity(aligned, numeric_cols)
        
        # Normalize
        final_df = normalize_to_zscore(stationary_df, numeric_cols)
        
        # Save
        output_path = os.path.join(self.processed_dir, 'aligned_timeseries.csv')
        save_to_csv(final_df, output_path)
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(output_path))
        loaded = pd.read_csv(output_path, index_col=0)
        self.assertGreater(len(loaded), 0)

if __name__ == '__main__':
    unittest.main()