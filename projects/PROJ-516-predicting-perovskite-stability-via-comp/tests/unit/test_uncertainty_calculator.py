"""
Unit tests for the uncertainty calculator module.
"""

import math
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from code.utils.uncertainty_calculator import (
    calculate_total_uncertainty,
    compute_uncertainties_for_dataframe,
    DEFAULT_PRECISION,
    DEFAULT_EXPERIMENTAL_ERROR
)
from code.utils.instrument_registry import get_precision

class TestUncertaintyCalculator(unittest.TestCase):
    """Test cases for uncertainty calculations."""

    def test_calculate_total_uncertainty_both_provided(self):
        """Test calculation when both precision and error are provided."""
        precision = 5.0
        experimental_error = 3.0
        expected = math.sqrt(5.0**2 + 3.0**2)

        result = calculate_total_uncertainty(precision, experimental_error)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_total_uncertainty_missing_precision(self):
        """Test calculation when precision is missing (should use default)."""
        experimental_error = 2.0
        expected = math.sqrt(DEFAULT_PRECISION**2 + experimental_error**2)

        result = calculate_total_uncertainty(None, experimental_error)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_total_uncertainty_missing_error(self):
        """Test calculation when experimental error is missing (should use 0)."""
        precision = 10.0
        expected = math.sqrt(precision**2 + DEFAULT_EXPERIMENTAL_ERROR**2)

        result = calculate_total_uncertainty(precision, None)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_total_uncertainty_both_missing(self):
        """Test calculation when both are missing (should use defaults)."""
        expected = DEFAULT_PRECISION  # sqrt(10^2 + 0^2) = 10

        result = calculate_total_uncertainty(None, None)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_total_uncertainty_invalid_precision(self):
        """Test calculation with invalid (negative) precision."""
        result = calculate_total_uncertainty(-5.0, 2.0)
        # Should use default precision
        expected = math.sqrt(DEFAULT_PRECISION**2 + 2.0**2)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_total_uncertainty_invalid_error(self):
        """Test calculation with invalid (negative) experimental error."""
        result = calculate_total_uncertainty(5.0, -3.0)
        # Should use default error (0)
        expected = math.sqrt(5.0**2 + DEFAULT_EXPERIMENTAL_ERROR**2)
        self.assertAlmostEqual(result, expected, places=6)

    def test_compute_uncertainties_for_dataframe(self):
        """Test DataFrame uncertainty computation."""
        # Create a mock DataFrame
        data = {
            'formula': ['CsPbI3', 'FAPbI3', 'MAPbBr3'],
            'T_d': [300, 320, 350],
            'instrument_model': ['TA Instruments', 'Mettler Toledo', 'Unknown Model']
        }
        df = pd.DataFrame(data)

        # Mock get_precision to return specific values
        with patch('code.utils.uncertainty_calculator.get_precision') as mock_get_precision:
            mock_get_precision.side_effect = lambda x: 5.0 if 'TA' in x else (10.0 if 'Mettler' in x else 15.0)

            result_df = compute_uncertainties_for_dataframe(df, 'instrument_model', None)

            # Check that total_uncertainty column was added
            self.assertIn('total_uncertainty', result_df.columns)

            # Check that all values are non-negative
            self.assertTrue((result_df['total_uncertainty'] >= 0).all())

            # Check that the column has the right length
            self.assertEqual(len(result_df['total_uncertainty']), len(df))

    def test_compute_uncertainties_with_experimental_error(self):
        """Test DataFrame computation with experimental error column."""
        data = {
            'formula': ['CsPbI3', 'FAPbI3'],
            'T_d': [300, 320],
            'instrument_model': ['TA Instruments', 'Mettler Toledo'],
            'experimental_error': [2.0, 3.0]
        }
        df = pd.DataFrame(data)

        with patch('code.utils.uncertainty_calculator.get_precision') as mock_get_precision:
            mock_get_precision.side_effect = lambda x: 5.0

            result_df = compute_uncertainties_for_dataframe(df, 'instrument_model', 'experimental_error')

            # Verify calculations manually for first row: sqrt(5^2 + 2^2) = sqrt(29)
            expected_first = math.sqrt(5.0**2 + 2.0**2)
            self.assertAlmostEqual(result_df.iloc[0]['total_uncertainty'], expected_first, places=6)

            # Verify calculations manually for second row: sqrt(5^2 + 3^2) = sqrt(34)
            expected_second = math.sqrt(5.0**2 + 3.0**2)
            self.assertAlmostEqual(result_df.iloc[1]['total_uncertainty'], expected_second, places=6)

    def test_compute_uncertainties_missing_columns(self):
        """Test behavior when columns are missing."""
        data = {
            'formula': ['CsPbI3'],
            'T_d': [300]
        }
        df = pd.DataFrame(data)

        # Should still work, using defaults
        result_df = compute_uncertainties_for_dataframe(df, 'nonexistent_col', 'nonexistent_col2')

        self.assertIn('total_uncertainty', result_df.columns)
        # Should be sqrt(10^2 + 0^2) = 10
        self.assertAlmostEqual(result_df.iloc[0]['total_uncertainty'], 10.0, places=6)

if __name__ == '__main__':
    unittest.main()