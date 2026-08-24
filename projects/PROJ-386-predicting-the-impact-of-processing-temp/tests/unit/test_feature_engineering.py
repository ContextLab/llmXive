"""
Unit tests for interaction feature generation in code/data/preprocess.py.

Specifically verifies:
1. The creation of interaction columns (e.g., 'Temperature_Mg').
2. The mathematical correctness of the interaction values (Temp * Mg).
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.preprocess import generate_interaction_features


class TestInteractionFeatureGeneration:
    """Tests for the generate_interaction_features function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'Temperature': [400.0, 500.0, 600.0],
            'Mg': [0.5, 1.0, 1.5],
            'Si': [0.3, 0.6, 0.9],
            'Cu': [0.1, 0.2, 0.3],
            'Grain_Size': [10.0, 12.0, 14.0]
        })
        
        # Expected interaction values for Temp * Mg
        self.expected_temp_mg = [400.0 * 0.5, 500.0 * 1.0, 600.0 * 1.5]
        # Expected interaction values for Temp * Si
        self.expected_temp_si = [400.0 * 0.3, 500.0 * 0.6, 600.0 * 0.9]

    def test_interaction_columns_created(self):
        """Verify that interaction columns are created in the output DataFrame."""
        result = generate_interaction_features(self.test_data)
        
        # Check that the new columns exist
        assert 'Temperature_Mg' in result.columns, "Interaction column 'Temperature_Mg' not found."
        assert 'Temperature_Si' in result.columns, "Interaction column 'Temperature_Si' not found."
        assert 'Temperature_Cu' in result.columns, "Interaction column 'Temperature_Cu' not found."

    def test_temp_mg_values_correct(self):
        """Verify the mathematical correctness of the Temp × Mg interaction."""
        result = generate_interaction_features(self.test_data)
        
        # Assert values match expected calculation
        pd.testing.assert_series_equal(
            result['Temperature_Mg'],
            pd.Series(self.expected_temp_mg, name='Temperature_Mg'),
            check_names=False
        )

    def test_temp_si_values_correct(self):
        """Verify the mathematical correctness of the Temp × Si interaction."""
        result = generate_interaction_features(self.test_data)
        
        # Assert values match expected calculation
        pd.testing.assert_series_equal(
            result['Temperature_Si'],
            pd.Series(self.expected_temp_si, name='Temperature_Si'),
            check_names=False
        )

    def test_original_columns_unchanged(self):
        """Verify that original data columns remain unchanged."""
        result = generate_interaction_features(self.test_data)
        
        # Check original columns are preserved
        assert 'Temperature' in result.columns
        assert 'Mg' in result.columns
        assert 'Si' in result.columns
        
        # Check values are identical to input
        pd.testing.assert_series_equal(result['Temperature'], self.test_data['Temperature'])
        pd.testing.assert_series_equal(result['Mg'], self.test_data['Mg'])

    def test_empty_dataframe(self):
        """Verify behavior with an empty DataFrame."""
        empty_df = pd.DataFrame(columns=['Temperature', 'Mg', 'Si'])
        result = generate_interaction_features(empty_df)
        
        # Should not crash and should return empty df with interaction columns
        assert 'Temperature_Mg' in result.columns
        assert len(result) == 0

    def test_missing_interaction_variable(self):
        """Verify behavior if one of the interaction variables (e.g., Mg) is missing."""
        df_missing_mg = pd.DataFrame({
            'Temperature': [400.0, 500.0],
            'Si': [0.3, 0.6]
        })
        
        # The function should handle missing columns gracefully (likely by skipping that interaction)
        # or raise a clear error. Based on typical implementation, it should skip missing ones.
        result = generate_interaction_features(df_missing_mg)
        
        # Temperature_Si should exist
        assert 'Temperature_Si' in result.columns
        # Temperature_Mg should NOT exist if Mg is missing (or handle gracefully)
        # Assuming the implementation skips missing columns:
        assert 'Temperature_Mg' not in result.columns

    def test_null_values_in_interaction(self):
        """Verify handling of null values in interaction calculation."""
        df_with_null = pd.DataFrame({
            'Temperature': [400.0, np.nan, 600.0],
            'Mg': [0.5, 1.0, np.nan],
            'Si': [0.3, 0.6, 0.9]
        })
        
        result = generate_interaction_features(df_with_null)
        
        # Check that the interaction column exists
        assert 'Temperature_Mg' in result.columns
        
        # Verify that nulls propagate correctly (NaN * x = NaN)
        assert pd.isna(result.loc[1, 'Temperature_Mg'])
        assert pd.isna(result.loc[2, 'Temperature_Mg'])