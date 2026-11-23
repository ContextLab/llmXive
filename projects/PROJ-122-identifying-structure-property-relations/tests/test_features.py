"""
Unit tests for User Story 2: Feature Engineering and Descriptor Generation.
Specifically covers T023: VIF calculation logic (diagnostic only).
"""

import unittest
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from pathlib import Path
import sys

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Mock the VIF calculation function if it doesn't exist in 02_features yet,
# or import it if T028a has been partially implemented.
# Since T028a is not yet done, we implement the logic here for the test to validate the LOGIC.
# The actual implementation in 02_features.py will be verified by T028a.

def calculate_vif_for_dataframe(df: pd.DataFrame, exclude_intercept: bool = True) -> pd.Series:
    """
    Calculates Variance Inflation Factor (VIF) for each feature in a DataFrame.
    
    This is a standalone implementation for testing purposes to ensure the logic
    works before it is integrated into 02_features.py.
    
    Args:
        df: DataFrame containing only numeric features.
        exclude_intercept: If True, the constant term is excluded from calculation.
        
    Returns:
        A pandas Series with feature names as index and VIF values as values.
    """
    X = df.values
    vif_data = []
    
    # If we want to include intercept in the model but not report its VIF,
    # we usually add a constant column. However, statsmodels VIF function
    # expects the design matrix.
    # Standard practice: Add constant, calculate, then drop the constant row from results.
    
    # Using statsmodels implementation directly as it is robust
    # We assume the input df already has no intercept column unless specified.
    # For VIF calculation, we typically add a constant column to the matrix X.
    
    # Note: statsmodels vif function expects the full design matrix.
    # We iterate over columns.
    
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
    except ImportError:
        raise ImportError("statsmodels is required for VIF calculation. Install it via requirements.txt.")

    vif_series = pd.Series(index=df.columns, dtype=float)
    
    for i, column in enumerate(df.columns):
        vif = variance_inflation_factor(X, i)
        vif_series[column] = vif
        
    return vif_series


class TestVIFCalculation(unittest.TestCase):
    """
    T023: Unit test for VIF calculation logic (diagnostic only).
    Verify VIF computation for a small matrix and flagging of values > 5.0.
    """

    def test_vif_calculation_perfectly_uncorrelated(self):
        """
        Test VIF on a matrix with orthogonal columns.
        Expected VIF should be close to 1.0.
        """
        np.random.seed(42)
        # Create 3 uncorrelated random columns
        data = {
            'A': np.random.randn(100),
            'B': np.random.randn(100),
            'C': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif_for_dataframe(df)
        
        # VIF should be close to 1 for uncorrelated data
        self.assertTrue(all(vif_results < 2.0), "VIF should be near 1 for uncorrelated data")
        self.assertTrue(all(vif_results > 0.5), "VIF must be positive")

    def test_vif_calculation_highly_correlated(self):
        """
        Test VIF on a matrix with one column being a linear combination of others.
        Expected VIF should be very high (> 5.0, likely > 10 or infinite).
        """
        np.random.seed(42)
        n = 100
        A = np.random.randn(n)
        B = np.random.randn(n)
        # C is almost perfectly correlated with A + B
        C = A + B + np.random.randn(n) * 0.001 
        
        data = {
            'A': A,
            'B': B,
            'C': C
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif_for_dataframe(df)
        
        # At least one VIF should be high (> 5.0)
        self.assertTrue(any(vif_results > 5.0), 
                        f"Expected at least one VIF > 5.0 for correlated data, got: {vif_results}")

    def test_vif_flagging_logic(self):
        """
        Test the logic for flagging predictors with VIF > 5.0.
        """
        np.random.seed(42)
        n = 100
        # Create data with one highly correlated pair
        A = np.random.randn(n)
        B = A * 0.9 + np.random.randn(n) * 0.1  # High correlation
        C = np.random.randn(n)
        
        data = {
            'A': A,
            'B': B,
            'C': C
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif_for_dataframe(df)
        
        # Define the threshold
        threshold = 5.0
        
        # Identify flagged features
        flagged_features = vif_results[vif_results > threshold]
        
        # Assert that B (and possibly A) are flagged
        self.assertIn('B', flagged_features.index, 
                      "Feature B should be flagged as VIF > 5.0")
        
        # Assert the count of flagged features is reasonable
        self.assertGreater(len(flagged_features), 0, 
                           "At least one feature should be flagged")

    def test_vif_empty_dataframe(self):
        """Test behavior with empty dataframe."""
        df = pd.DataFrame()
        with self.assertRaises((ValueError, IndexError)):
            calculate_vif_for_dataframe(df)

    def test_vif_single_column(self):
        """Test behavior with a single column (VIF is undefined or 1.0 depending on implementation)."""
        df = pd.DataFrame({'A': np.random.randn(10)})
        vif_results = calculate_vif_for_dataframe(df)
        # With a single column, VIF is typically 1.0 (no other variables to collineate with)
        self.assertEqual(vif_results['A'], 1.0)

    def test_vif_threshold_boundary(self):
        """Test that values exactly at 5.0 are handled correctly (strictly greater)."""
        # Create a scenario where VIF is likely to be exactly or near 5.0
        # This is hard to control precisely, so we test the logic with a mock result
        # rather than generating data that hits exactly 5.0.
        
        # Instead, we verify the filtering logic directly
        vif_series = pd.Series({'A': 4.9, 'B': 5.0, 'C': 5.1})
        threshold = 5.0
        
        flagged = vif_series[vif_series > threshold]
        
        self.assertNotIn('A', flagged.index)
        self.assertNotIn('B', flagged.index) # 5.0 is not > 5.0
        self.assertIn('C', flagged.index)

if __name__ == '__main__':
    unittest.main()