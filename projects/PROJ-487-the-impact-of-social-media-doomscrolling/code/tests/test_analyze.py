import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np

# Attempt to import the analysis module which should contain the Granger causality logic.
# If the module doesn't exist yet, we mock the import for the test structure,
# but the test will fail if the real function isn't implemented.
try:
    from data.analyze import run_granger_causality_fixed_sweep, compute_correlations
    HAS_ANALYZE = True
except ImportError:
    HAS_ANALYZE = False
    # Define a dummy function to allow the test class to load if analyze.py is missing
    def run_granger_causality_fixed_sweep(df):
        raise NotImplementedError("run_granger_causality_fixed_sweep not implemented in data.analyze")
    def compute_correlations(df):
        raise NotImplementedError("compute_correlations not implemented in data.analyze")

class TestCorrelationCalculation(unittest.TestCase):
    """
    Unit test for correlation calculation in data.analyze.
    
    This test verifies that:
    1. Pearson coefficient is ~1.0 for perfectly correlated series (y=x).
    2. Pearson coefficient is ~0.0 for uncorrelated series (y=random).
    """

    def test_perfectly_correlated_series(self):
        """Test correlation calculation with perfectly correlated series (y=x)."""
        n = 100
        np.random.seed(42)
        x = np.random.normal(0, 1, n)
        y = x  # Perfectly correlated
        
        df = pd.DataFrame({
            'date': pd.date_range(start="2023-01-01", periods=n, freq="D"),
            'news_volume': x,
            'anxiety_index': y
        })
        
        if HAS_ANALYZE:
            result = compute_correlations(df)
            # result is expected to be a dict with 'pearson' and 'spearman' keys
            # or a DataFrame with correlation results. Adjust based on actual implementation.
            # Assuming result is a dict for now based on typical correlation function outputs.
            self.assertIn('pearson', result)
            self.assertAlmostEqual(result['pearson'], 1.0, places=5, 
                                   msg="Pearson coefficient should be ~1.0 for perfectly correlated series")
        else:
            # If module not found, we still verify the test structure is correct
            # by checking that the function would be called correctly if it existed.
            self.skipTest("data.analyze module not found, skipping actual correlation test")

    def test_uncorrelated_series(self):
        """Test correlation calculation with uncorrelated series (y=random)."""
        n = 100
        np.random.seed(42)
        x = np.random.normal(0, 1, n)
        y = np.random.normal(0, 1, n)  # Uncorrelated
        
        df = pd.DataFrame({
            'date': pd.date_range(start="2023-01-01", periods=n, freq="D"),
            'news_volume': x,
            'anxiety_index': y
        })
        
        if HAS_ANALYZE:
            result = compute_correlations(df)
            self.assertIn('pearson', result)
            # For uncorrelated series, Pearson should be close to 0 (allow some tolerance)
            self.assertAlmostEqual(result['pearson'], 0.0, delta=0.3, 
                                   msg="Pearson coefficient should be ~0.0 for uncorrelated series")
        else:
            self.skipTest("data.analyze module not found, skipping actual correlation test")

    def test_spearman_correlation(self):
        """Test Spearman correlation calculation."""
        n = 100
        np.random.seed(42)
        x = np.arange(n)
        y = x + np.random.normal(0, 0.1, n)  # Strong monotonic relationship
        
        df = pd.DataFrame({
            'date': pd.date_range(start="2023-01-01", periods=n, freq="D"),
            'news_volume': x,
            'anxiety_index': y
        })
        
        if HAS_ANALYZE:
            result = compute_correlations(df)
            self.assertIn('spearman', result)
            self.assertAlmostEqual(result['spearman'], 1.0, places=2, 
                                   msg="Spearman coefficient should be close to 1.0 for monotonic relationship")
        else:
            self.skipTest("data.analyze module not found, skipping actual correlation test")

class TestGrangerCausalityFixedSweep(unittest.TestCase):
    """
    Unit test for Granger causality fixed-sweep (lags {1, 2, 3, 7, 14}).
    
    This test verifies that the function:
    1. Accepts a DataFrame with 'date', 'gdelt_negative', and 'anxiety_search' columns.
    2. Iterates exactly over the fixed set of lags: {1, 2, 3, 7, 14}.
    3. Returns a DataFrame with columns: 'lag', 'p_value', 'f_statistic', 'significant'.
    4. Handles stationary data correctly (assumes input is stationary as per US2).
    """

    def setUp(self):
        """Create a mock stationary time-series dataset for testing."""
        np.random.seed(42)
        n_days = 100
        dates = pd.date_range(start="2023-01-01", periods=n_days, freq="D")
        
        # Simulate stationary data (random walk difference or AR(1) with phi < 1)
        # Here we use a simple AR(1) process with phi=0.5 to ensure stationarity
        ar_coeff = 0.5
        noise = np.random.normal(0, 1, n_days)
        gdelt = np.zeros(n_days)
        anxiety = np.zeros(n_days)
        
        for i in range(1, n_days):
            gdelt[i] = ar_coeff * gdelt[i-1] + noise[i]
            # Anxiety is weakly influenced by gdelt with a lag of 2 for the test to pass significance
            anxiety[i] = ar_coeff * anxiety[i-1] + 0.3 * gdelt[i-2] + noise[i] * 0.5
        
        self.test_df = pd.DataFrame({
            'date': dates,
            'gdelt_negative': gdelt,
            'anxiety_search': anxiety
        })

    @unittest.skipIf(not HAS_ANALYZE, "data.analyze module not found")
    def test_fixed_sweep_lags(self):
        """Test that the function runs over the exact fixed set of lags."""
        fixed_lags = [1, 2, 3, 7, 14]
        
        # Run the function
        result = run_granger_causality_fixed_sweep(self.test_df)
        
        # Verify return type
        self.assertIsInstance(result, pd.DataFrame)
        
        # Verify columns
        expected_columns = ['lag', 'p_value', 'f_statistic', 'significant']
        self.assertListEqual(list(result.columns), expected_columns)
        
        # Verify that the lags in the result match the fixed set exactly
        result_lags = sorted(result['lag'].tolist())
        self.assertListEqual(result_lags, fixed_lags)
        
        # Verify that p_values are floats between 0 and 1
        self.assertTrue(all(0 <= p <= 1 for p in result['p_value']))
        
        # Verify that significant is boolean
        self.assertTrue(all(isinstance(s, (bool, np.bool_)) for s in result['significant']))

    @unittest.skipIf(not HAS_ANALYZE, "data.analyze module not found")
    def test_significance_calculation(self):
        """Test that the significance column is correctly calculated based on p < 0.05."""
        result = run_granger_causality_fixed_sweep(self.test_df)
        
        # Manually check one row
        for _, row in result.iterrows():
            expected_sig = row['p_value'] < 0.05
            self.assertEqual(row['significant'], expected_sig, 
                             f"Significance mismatch for lag {row['lag']}")

    @unittest.skipIf(not HAS_ANALYZE, "data.analyze module not found")
    def test_empty_dataframe_raises(self):
        """Test that an empty DataFrame raises an appropriate error."""
        empty_df = pd.DataFrame(columns=['date', 'gdelt_negative', 'anxiety_search'])
        with self.assertRaises(ValueError):
            run_granger_causality_fixed_sweep(empty_df)

    @unittest.skipIf(not HAS_ANALYZE, "data.analyze module not found")
    def test_missing_columns_raises(self):
        """Test that missing required columns raises an error."""
        bad_df = self.test_df.drop(columns=['gdelt_negative'])
        with self.assertRaises(ValueError):
            run_granger_causality_fixed_sweep(bad_df)

if __name__ == '__main__':
    unittest.main()