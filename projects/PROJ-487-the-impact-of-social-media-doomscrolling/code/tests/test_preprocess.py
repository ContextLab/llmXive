import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.stattools import adfuller

# Ensure the project root is in the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.preprocess import test_stationarity, ensure_stationarity, align_timestamps

class TestTimestampAlignment(unittest.TestCase):
    """Existing test class for timestamp alignment (T016)."""
    
    def test_timestamp_alignment_intersection(self):
        """Test that align_timestamps returns only the intersection of dates."""
        
        # Create two dataframes with overlapping date ranges
        # Range 1: 2020-01-01 to 2020-06-30
        dates1 = pd.date_range(start='2020-01-01', end='2020-06-30', freq='D')
        # Range 2: 2020-03-01 to 2020-09-30
        dates2 = pd.date_range(start='2020-03-01', end='2020-09-30', freq='D')
        
        # Create distinct values to verify preservation
        # Use a simple formula so we can predict values if needed, 
        # but primarily checking the date range intersection.
        np.random.seed(42)
        df1 = pd.DataFrame({
            'date': dates1, 
            'gdelt_count': np.random.rand(len(dates1)) * 100
        })
        df2 = pd.DataFrame({
            'date': dates2, 
            'trends_score': np.random.rand(len(dates2)) * 100
        })
        
        # Include a zero value in the intersection to verify preservation logic
        # Find a date in the intersection (e.g., 2020-03-15)
        intersection_start = pd.Timestamp('2020-03-01')
        test_date_idx = (intersection_start - dates1[0]).days
        df1.loc[test_date_idx, 'gdelt_count'] = 0.0
        
        result = align_timestamps(df1, df2)
        
        # Verify the result contains only dates from 2020-03-01 to 2020-06-30
        expected_start = pd.Timestamp('2020-03-01')
        expected_end = pd.Timestamp('2020-06-30')
        
        self.assertEqual(result['date'].min(), expected_start, 
                         f"Start date {result['date'].min()} should be {expected_start}")
        self.assertEqual(result['date'].max(), expected_end, 
                         f"End date {result['date'].max()} should be {expected_end}")
        
        # Calculate expected length: inclusive of start and end
        expected_length = (expected_end - expected_start).days + 1
        self.assertEqual(len(result), expected_length, 
                         f"Length {len(result)} should be {expected_length}")
        
        # Verify zero values are preserved (not interpolated to non-zero)
        # Check the specific row where we set 0.0 in df1
        # In the result, the date should be 2020-03-15 (or similar in range)
        # We check that the value is 0.0, not interpolated to something else
        mask = result['date'] == pd.Timestamp('2020-03-15')
        if mask.any():
            val = result.loc[mask, 'gdelt_count'].iloc[0]
            self.assertEqual(val, 0.0, "Zero value should be preserved, not interpolated")
        
        # Verify that columns are correctly aligned
        self.assertIn('gdelt_count', result.columns)
        self.assertIn('trends_score', result.columns)
        self.assertIn('date', result.columns)

class TestADFStationarity(unittest.TestCase):
    """Test class for ADF test and differencing logic (T017)."""

    def test_adf_differencing(self):
        """
        Unit test for ADF test and differencing logic.
        
        Mock: A non-stationary series (random walk).
        Assertion: Verify the function detects non-stationarity (p >= 0.05) 
        and returns the differenced series which passes ADF (p < 0.05).
        """
        # Create a non-stationary series: a random walk
        np.random.seed(42)
        n = 100
        noise = np.random.normal(0, 1, n)
        random_walk = np.cumsum(noise)
        
        # Create a DataFrame mimicking the expected input format
        dates = pd.date_range(start='2020-01-01', periods=n, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'value': random_walk
        })
        
        # Test 1: Verify that the original series is detected as non-stationary
        is_stationary, p_value = test_stationarity(df['value'])
        self.assertFalse(is_stationary, "Original random walk should be non-stationary (p >= 0.05)")
        self.assertGreaterEqual(p_value, 0.05, f"ADF p-value {p_value} should be >= 0.05 for non-stationary series")
        
        # Test 2: Verify that the function ensures stationarity via differencing
        # We use ensure_stationarity which should apply differencing until stationary
        stationary_series, diff_order = ensure_stationarity(df['value'])
        
        # The differenced series should be stationary
        is_diff_stationary, diff_p_value = test_stationarity(stationary_series)
        self.assertTrue(is_diff_stationary, "Differenced series should be stationary (p < 0.05)")
        self.assertLess(diff_p_value, 0.05, f"Differenced series ADF p-value {diff_p_value} should be < 0.05")
        
        # Verify that at least one differencing was applied (since random walk is non-stationary)
        self.assertGreater(diff_order, 0, "Differencing order should be > 0 for a random walk")

if __name__ == '__main__':
    unittest.main()