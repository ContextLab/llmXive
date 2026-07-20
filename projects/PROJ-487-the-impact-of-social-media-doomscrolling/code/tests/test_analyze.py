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
    from data.analyze import granger_causality_fixed_sweep
    HAS_ANALYZE = True
except ImportError:
    HAS_ANALYZE = False
    # Define a dummy function to allow the test class to load if analyze.py is missing
    def granger_causality_fixed_sweep(df):
        raise NotImplementedError("granger_causality_fixed_sweep not implemented in data.analyze")

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
        result = granger_causality_fixed_sweep(self.test_df)
        
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
        result = granger_causality_fixed_sweep(self.test_df)
        
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
            granger_causality_fixed_sweep(empty_df)

    @unittest.skipIf(not HAS_ANALYZE, "data.analyze module not found")
    def test_missing_columns_raises(self):
        """Test that missing required columns raises an error."""
        bad_df = self.test_df.drop(columns=['gdelt_negative'])
        with self.assertRaises(ValueError):
            granger_causality_fixed_sweep(bad_df)

if __name__ == '__main__':
    unittest.main()