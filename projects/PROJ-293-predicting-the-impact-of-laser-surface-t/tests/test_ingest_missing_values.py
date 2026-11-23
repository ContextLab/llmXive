import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingest import handle_missing_values

class TestMissingValueHandling:
    """
    Test cases for FR-002: Missing value handling logic.
    """

    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe with various missing value scenarios."""
        data = {
            'pulse_duration': [10.0, 20.0, np.nan, 40.0, 50.0, 60.0],
            'power': [100.0, 200.0, 300.0, np.nan, 500.0, 600.0],
            'scanning_speed': [10.0, 20.0, 30.0, 40.0, np.nan, 60.0],
            'pattern_geometry': ['circle', 'square', 'circle', 'square', 'circle', 'square'],
            'hardness': [200.0, 300.0, 400.0, 500.0, 600.0, np.nan],
            'elastic_modulus': [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
            'contact_load': [10.0, np.nan, 30.0, 40.0, 50.0, 60.0],
            'sliding_speed': [0.1, 0.2, 0.3, np.nan, 0.5, 0.6],
            'wear_rate': [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
        }
        return pd.DataFrame(data)

    def test_drop_missing_predictors(self, sample_data):
        """
        Verify that records with missing predictor values are dropped.
        Predictors: pulse_duration, power, scanning_speed, pattern_geometry, hardness, elastic_modulus
        """
        result = handle_missing_values(sample_data)
        
        # Original data has 6 rows
        # Row 2 (index 2) has missing pulse_duration -> DROP
        # Row 3 (index 3) has missing power -> DROP
        # Row 4 (index 4) has missing scanning_speed -> DROP
        # Row 5 (index 5) has missing hardness -> DROP
        # Expected remaining: Row 0, Row 1
        expected_rows = 2
        
        assert len(result) == expected_rows, f"Expected {expected_rows} rows, got {len(result)}"
        
        # Verify no missing predictors remain
        predictors = ['pulse_duration', 'power', 'scanning_speed', 'pattern_geometry', 'hardness', 'elastic_modulus']
        for col in predictors:
            assert not result[col].isna().any(), f"Predictor {col} still has missing values"

    def test_retain_missing_normalization_inputs(self, sample_data):
        """
        Verify that records with missing contact_load or sliding_speed are retained
        but marked with normalization_method='raw'.
        """
        result = handle_missing_values(sample_data)
        
        # Row 1 (index 1) has missing contact_load -> RETAIN, set to 'raw'
        # Row 3 (index 3) has missing sliding_speed -> RETAIN, set to 'raw' (but this row is dropped due to missing power)
        # After dropping missing predictors, only Row 0 and Row 1 should remain.
        # Row 0: contact_load=10.0, sliding_speed=0.1 -> 'normalized'
        # Row 1: contact_load=NaN, sliding_speed=0.2 -> 'raw'
        
        assert len(result) == 2, "Should have 2 rows after dropping missing predictors"
        
        # Check normalization_method for Row 1 (originally index 1)
        # In the result, it should be the second row (index 1)
        assert result.iloc[1]['normalization_method'] == 'raw', "Record with missing contact_load should be marked as 'raw'"
        
        # Check normalization_method for Row 0
        assert result.iloc[0]['normalization_method'] == 'normalized', "Record with complete data should be 'normalized'"

    def test_drop_missing_target(self, sample_data):
        """
        Verify that records with missing wear_rate (target) are dropped.
        """
        # Modify sample data to have missing wear_rate
        sample_data.loc[0, 'wear_rate'] = np.nan
        
        result = handle_missing_values(sample_data)
        
        # Row 0 has missing wear_rate -> DROP
        # Row 2, 3, 4, 5 have missing predictors -> DROP
        # Only Row 1 should remain (if it doesn't have missing predictors)
        # Row 1: power=200, scanning_speed=20, etc. -> No missing predictors
        # But Row 1 has missing contact_load -> RETAIN as 'raw'
        
        expected_rows = 1
        assert len(result) == expected_rows, f"Expected {expected_rows} rows, got {len(result)}"

    def test_all_normalization_columns_missing(self):
        """
        Test scenario where contact_load and sliding_speed are completely missing from the dataset.
        All records should be marked as 'raw'.
        """
        data = {
            'pulse_duration': [10.0, 20.0],
            'power': [100.0, 200.0],
            'scanning_speed': [10.0, 20.0],
            'pattern_geometry': ['circle', 'square'],
            'hardness': [200.0, 300.0],
            'elastic_modulus': [100.0, 200.0],
            'wear_rate': [0.01, 0.02]
            # No contact_load or sliding_speed columns
        }
        df = pd.DataFrame(data)
        
        result = handle_missing_values(df)
        
        assert len(result) == 2, "Should retain all rows (no missing predictors)"
        assert all(result['normalization_method'] == 'raw'), "All records should be 'raw' when normalization columns are missing"

    def test_normalization_method_column_exists(self, sample_data):
        """
        Verify that the 'normalization_method' column is created.
        """
        result = handle_missing_values(sample_data)
        assert 'normalization_method' in result.columns, "normalization_method column should exist"
        
        # Check that values are either 'normalized' or 'raw'
        valid_values = {'normalized', 'raw'}
        assert all(val in valid_values for val in result['normalization_method']), \
            f"normalization_method should only contain {valid_values}"
