"""
Unit tests for T016: Empirical Coverage Calculation.

Tests the calculate_coverage_batch and save_coverage_results functions
in code/metrics.py to ensure they correctly compute empirical coverage.
"""

import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from code.metrics import calculate_coverage_batch, save_coverage_results, empirical_coverage


class TestEmpiricalCoverage(unittest.TestCase):
    
    def test_all_inside(self):
        """All actuals inside the interval -> coverage 1.0"""
        lower = np.array([0.0, 0.0, 0.0])
        upper = np.array([10.0, 10.0, 10.0])
        actual = np.array([2.0, 5.0, 8.0])
        cov = empirical_coverage(lower, upper, actual)
        self.assertEqual(cov, 1.0)

    def test_all_outside(self):
        """All actuals outside the interval -> coverage 0.0"""
        lower = np.array([0.0, 0.0, 0.0])
        upper = np.array([2.0, 2.0, 2.0])
        actual = np.array([5.0, 6.0, 7.0])
        cov = empirical_coverage(lower, upper, actual)
        self.assertEqual(cov, 0.0)

    def test_partial_coverage(self):
        """50% inside -> coverage 0.5"""
        lower = np.array([0.0, 0.0])
        upper = np.array([5.0, 5.0])
        actual = np.array([2.0, 6.0])
        cov = empirical_coverage(lower, upper, actual)
        self.assertEqual(cov, 0.5)

    def test_nan_raises_error(self):
        """NaN values should raise ValueError"""
        lower = np.array([0.0, np.nan])
        upper = np.array([10.0, 10.0])
        actual = np.array([2.0, 5.0])
        with self.assertRaises(ValueError):
            empirical_coverage(lower, upper, actual)

    def test_length_mismatch_raises_error(self):
        """Different lengths should raise ValueError"""
        lower = np.array([0.0])
        upper = np.array([10.0])
        actual = np.array([2.0, 5.0])
        with self.assertRaises(ValueError):
            empirical_coverage(lower, upper, actual)


class TestCalculateCoverageBatch(unittest.TestCase):
    
    def setUp(self):
        """Setup test data for batch coverage calculation."""
        # Create mock interval data
        # Format: series_id, model, horizon, lower (list), upper (list)
        self.intervals_data = {
            'series_id': ['S1', 'S1', 'S2'],
            'model': ['ARIMA', 'ARIMA', 'ETS'],
            'horizon': [1, 2, 1],
            'lower': [
                [1.0, 2.0, 3.0],  # 3 test points for S1, h=1
                [4.0, 5.0],       # 2 test points for S1, h=2
                [10.0, 11.0, 12.0] # 3 test points for S2, h=1
            ],
            'upper': [
                [5.0, 6.0, 7.0],
                [8.0, 9.0],
                [14.0, 15.0, 16.0]
            ]
        }
        self.intervals_df = pd.DataFrame(self.intervals_data)

        # Create mock actuals data
        # Format: series_id, horizon, actual_value
        self.actuals_data = {
            'series_id': ['S1', 'S1', 'S1', 'S1', 'S1', 'S2', 'S2', 'S2'],
            'horizon': [1, 1, 1, 2, 2, 1, 1, 1],
            'actual_value': [2.0, 6.0, 8.0, 3.0, 9.5, 11.0, 15.0, 20.0]
        }
        # S1, h=1: actuals [2, 6, 8]. Intervals [1-5, 2-6, 3-7]. 
        #   2 in [1,5] (Yes), 6 in [2,6] (Yes), 8 in [3,7] (No). Coverage = 2/3
        # S1, h=2: actuals [3, 9.5]. Intervals [4-8, 5-9].
        #   3 in [4,8] (No), 9.5 in [5,9] (No). Coverage = 0/2 = 0.0
        # S2, h=1: actuals [11, 15, 20]. Intervals [10-14, 11-15, 12-16].
        #   11 in [10,14] (Yes), 15 in [11,15] (Yes), 20 in [12,16] (No). Coverage = 2/3

        self.actuals_df = pd.DataFrame(self.actuals_data)

    def test_batch_coverage_calculation(self):
        """Test that coverage is calculated correctly for multiple series/models."""
        result = calculate_coverage_batch(self.intervals_df, self.actuals_df)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(set(result.columns), {'series_id', 'model', 'horizon', 'empirical_coverage'})
        
        # Check S1, ARIMA, h=1 -> 2/3
        s1_h1 = result[(result['series_id'] == 'S1') & (result['horizon'] == 1)]
        self.assertAlmostEqual(s1_h1['empirical_coverage'].iloc[0], 2/3, places=5)
        
        # Check S1, ARIMA, h=2 -> 0/2
        s1_h2 = result[(result['series_id'] == 'S1') & (result['horizon'] == 2)]
        self.assertAlmostEqual(s1_h2['empirical_coverage'].iloc[0], 0.0, places=5)
        
        # Check S2, ETS, h=1 -> 2/3
        s2_h1 = result[(result['series_id'] == 'S2') & (result['horizon'] == 1)]
        self.assertAlmostEqual(s2_h1['empirical_coverage'].iloc[0], 2/3, places=5)

    def test_missing_actuals(self):
        """Test behavior when actuals are missing for a series/horizon."""
        # Remove actuals for S1, h=2
        actuals_subset = self.actuals_df[self.actuals_df['horizon'] != 2]
        result = calculate_coverage_batch(self.intervals_df, actuals_subset)
        
        # S1, h=2 should not be in the result
        self.assertFalse(((result['series_id'] == 'S1') & (result['horizon'] == 2)).any())
        self.assertEqual(len(result), 2)

    def test_length_mismatch_warning(self):
        """Test that length mismatch logs a warning and skips the record."""
        # Modify intervals to have mismatched length
        bad_intervals = self.intervals_df.copy()
        bad_intervals.loc[bad_intervals['series_id'] == 'S1', 'lower'] = [[1.0]] # Only 1 value
        bad_intervals.loc[bad_intervals['series_id'] == 'S1', 'upper'] = [[5.0]]
        
        result = calculate_coverage_batch(bad_intervals, self.actuals_df)
        # S1, h=1 should be skipped due to length mismatch
        self.assertFalse(((result['series_id'] == 'S1') & (result['horizon'] == 1)).any())


class TestSaveCoverageResults(unittest.TestCase):
    
    def test_save_to_csv(self):
        """Test that results are saved to a CSV file correctly."""
        df = pd.DataFrame({
            'series_id': ['S1'],
            'model': ['ARIMA'],
            'horizon': [1],
            'empirical_coverage': [0.5]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_coverage.csv')
            save_coverage_results(df, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            loaded_df = pd.read_csv(output_path)
            self.assertEqual(len(loaded_df), 1)
            self.assertAlmostEqual(loaded_df['empirical_coverage'].iloc[0], 0.5)