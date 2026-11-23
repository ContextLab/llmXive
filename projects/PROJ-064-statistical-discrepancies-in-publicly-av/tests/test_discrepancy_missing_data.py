import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from discrepancy import DiscrepancyCalculator
from exceptions import MissingDataError

class TestMissingDataHandling:
    """
    Tests for T020: Missing data handling in discrepancy.py.
    Verifies flagging and imputation strategies.
    """

    @pytest.fixture
    def sample_data_with_missing(self):
        return pd.DataFrame({
            'jurisdiction': ['A', 'B', 'C', 'D', 'E'],
            'precinct_sum': [1000.0, 2000.0, np.nan, 4000.0, 5000.0],
            'county_reported': [1000.0, 1950.0, 3000.0, np.nan, 4900.0]
        })

    def test_flag_strategy_marks_missing(self, sample_data_with_missing):
        """
        Test that 'flag' strategy marks rows with missing data 
        and sets discrepancy to NaN without crashing.
        """
        calculator = DiscrepancyCalculator({'imputation_strategy': 'flag'})
        result = calculator.calculate_discrepancies(sample_data_with_missing)

        # Check schema
        assert 'missing_data' in result.columns
        assert 'discrepancy_abs' in result.columns
        assert 'discrepancy_pct' in result.columns

        # Row C (index 2) has missing precinct_sum
        # Row D (index 3) has missing county_reported
        assert result.loc[2, 'missing_data'] is True
        assert result.loc[3, 'missing_data'] is True
        
        # Rows A, B, E should not be marked missing
        assert result.loc[0, 'missing_data'] is False
        assert result.loc[1, 'missing_data'] is False
        assert result.loc[4, 'missing_data'] is False

        # Discrepancies for missing rows should be NaN
        assert pd.isna(result.loc[2, 'discrepancy_abs'])
        assert pd.isna(result.loc[3, 'discrepancy_abs'])

        # Discrepancies for valid rows should be calculated
        assert result.loc[0, 'discrepancy_abs'] == 0.0
        assert result.loc[1, 'discrepancy_abs'] == 50.0

    def test_impute_strategy_fills_missing(self, sample_data_with_missing):
        """
        Test that 'impute' strategy fills missing values with median
        and marks missing_data as False.
        """
        calculator = DiscrepancyCalculator({'imputation_strategy': 'impute'})
        result = calculator.calculate_discrepancies(sample_data_with_missing)

        # Check that no rows are marked missing
        assert result['missing_data'].sum() == 0

        # Check that values were filled
        # Median of precinct_sum (1000, 2000, 4000, 5000) -> 3000
        # Median of county_reported (1000, 1950, 3000, 4900) -> 2475
        assert result.loc[2, 'precinct_sum'] == 3000.0
        assert result.loc[3, 'county_reported'] == 2475.0

        # Check discrepancies are calculated
        assert not pd.isna(result.loc[2, 'discrepancy_abs'])
        assert not pd.isna(result.loc[3, 'discrepancy_abs'])

    def test_impute_with_custom_fill(self, sample_data_with_missing):
        """
        Test imputation with a specific fill value.
        """
        calculator = DiscrepancyCalculator({
            'imputation_strategy': 'impute',
            'fill_value': 0.0
        })
        result = calculator.calculate_discrepancies(sample_data_with_missing)

        assert result.loc[2, 'precinct_sum'] == 0.0
        assert result.loc[3, 'county_reported'] == 0.0

    def test_impute_fails_on_all_null(self):
        """
        Test that imputation raises MissingDataError if all values in a column are null.
        """
        data = pd.DataFrame({
            'jurisdiction': ['A', 'B'],
            'precinct_sum': [np.nan, np.nan],
            'county_reported': [1000.0, 2000.0]
        })
        
        calculator = DiscrepancyCalculator({'imputation_strategy': 'impute'})
        
        with pytest.raises(MissingDataError, match="Imputation requested but median calculation failed"):
            calculator.calculate_discrepancies(data)

    def test_filter_missing_data_helper(self, sample_data_with_missing):
        """
        Test the filter_missing_data helper method.
        """
        calculator = DiscrepancyCalculator({'imputation_strategy': 'flag'})
        result = calculator.calculate_discrepancies(sample_data_with_missing)
        
        # Filter to keep only missing
        missing_only = calculator.filter_missing_data(result, keep_missing=True)
        assert len(missing_only) == 2
        assert missing_only['missing_data'].all()
        
        # Filter to drop missing
        clean_only = calculator.filter_missing_data(result, keep_missing=False)
        assert len(clean_only) == 3
        assert not clean_only['missing_data'].any()

    def test_schema_integrity(self, sample_data_with_missing):
        """
        Ensure output schema matches T007 requirements.
        """
        calculator = DiscrepancyCalculator({'imputation_strategy': 'flag'})
        result = calculator.calculate_discrepancies(sample_data_with_missing)
        
        required_cols = ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data']
        for col in required_cols:
            assert col in result.columns, f"Missing required column: {col}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])