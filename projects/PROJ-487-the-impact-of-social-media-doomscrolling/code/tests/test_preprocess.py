import unittest
import sys
import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.preprocess import align_timestamps

class TestTimestampAlignment(unittest.TestCase):

    def setUp(self):
        """Create sample dataframes for testing."""
        # GDELT data: sparse dates, some gaps
        self.df_gdelt = pd.DataFrame({
            'date': [
                datetime(2023, 1, 1),
                datetime(2023, 1, 3), # Gap on Jan 2
                datetime(2023, 1, 5), # Gap on Jan 4
                datetime(2023, 1, 7)
            ],
            'count': [10, 0, 5, 12] # Note: Jan 3 has 0 events explicitly
        })

        # Google Trends data: different sparse dates
        self.df_trends = pd.DataFrame({
            'date': [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 4), # Gap on Jan 3
                datetime(2023, 1, 7)
            ],
            'value': [50.0, 52.0, 55.0, 60.0]
        })

    def test_full_date_range_creation(self):
        """Test that the output covers the full range from min to max date."""
        result = align_timestamps(self.df_gdelt, self.df_trends)
        
        min_expected = min(self.df_gdelt['date'].min(), self.df_trends['date'].min())
        max_expected = max(self.df_gdelt['date'].max(), self.df_trends['date'].max())
        
        self.assertEqual(result['date'].min(), min_expected)
        self.assertEqual(result['date'].max(), max_expected)
        # Count days: Jan 1 to Jan 7 is 7 days
        self.assertEqual(len(result), 7)

    def test_zero_event_preservation(self):
        """Test that explicit zeros in GDELT are preserved and not interpolated."""
        result = align_timestamps(self.df_gdelt, self.df_trends)
        
        # Jan 3 has explicit 0 in source
        jan3_row = result[result['date'] == datetime(2023, 1, 3)]
        self.assertEqual(jan3_row['count'].values[0], 0)

    def test_gap_filling_gdelt(self):
        """Test that missing GDELT dates are filled with 0 (zero-event days)."""
        result = align_timestamps(self.df_gdelt, self.df_trends)
        
        # Jan 2 and Jan 4 were missing in GDELT source
        jan2_row = result[result['date'] == datetime(2023, 1, 2)]
        jan4_row = result[result['date'] == datetime(2023, 1, 4)]
        
        self.assertEqual(jan2_row['count'].values[0], 0)
        self.assertEqual(jan4_row['count'].values[0], 0)

    def test_linear_interpolation_trends(self):
        """Test that missing Google Trends values are linearly interpolated."""
        result = align_timestamps(self.df_gdelt, self.df_trends)
        
        # Jan 3 was missing in Trends source (between Jan 2=52 and Jan 4=55)
        # Linear interpolation: (52 + 55) / 2 = 53.5
        jan3_row = result[result['date'] == datetime(2023, 1, 3)]
        expected_value = 53.5
        self.assertAlmostEqual(jan3_row['value'].values[0], expected_value, places=1)

    def test_no_nan_in_result(self):
        """Test that the final result has no NaN values in metric columns."""
        result = align_timestamps(self.df_gdelt, self.df_trends)
        self.assertFalse(result['count'].isnull().any())
        self.assertFalse(result['value'].isnull().any())

    def test_different_column_names(self):
        """Test alignment when column names vary (e.g., 'value' vs 'count')."""
        # This test relies on the robust column selection logic in align_timestamps
        df_gdelt_alt = self.df_gdelt.rename(columns={'count': 'events'})
        df_trends_alt = self.df_trends.rename(columns={'value': 'index'})
        
        result = align_timestamps(df_gdelt_alt, df_trends_alt)
        self.assertEqual(len(result), 7)
        self.assertFalse(result.isnull().any().any())

if __name__ == '__main__':
    unittest.main()
