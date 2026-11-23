import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import validate_reflectance_range, apply_atmospheric_correction

class TestValidateReflectanceRange:
    """
    Unit tests for T011b: Validate atmospheric correction output.
    Asserts that values outside [0, 1] are clipped or rejected.
    """

    def test_values_within_range_unchanged(self):
        """Test that valid values in [0, 1] are not modified."""
        df = pd.DataFrame({
            'reflectance': [0.0, 0.25, 0.5, 0.75, 1.0]
        })
        result_df, count = validate_reflectance_range(df, column='reflectance')
        
        assert count == 0, "Should not clip values within range."
        assert result_df['reflectance'].equals(df['reflectance']), "Values should be unchanged."
        assert result_df['reflectance'].min() >= 0.0
        assert result_df['reflectance'].max() <= 1.0

    def test_values_below_zero_clipped(self):
        """Test that values below 0 are clipped to 0."""
        df = pd.DataFrame({
            'reflectance': [-0.5, -0.1, 0.0, 0.5]
        })
        result_df, count = validate_reflectance_range(df, column='reflectance')
        
        assert count == 2, "Should detect 2 values below 0."
        assert result_df['reflectance'].iloc[0] == 0.0, "Negative value should be clipped to 0."
        assert result_df['reflectance'].iloc[1] == 0.0, "Negative value should be clipped to 0."
        assert result_df['reflectance'].iloc[2] == 0.0
        assert result_df['reflectance'].iloc[3] == 0.5
        
        # Assert final range
        assert result_df['reflectance'].min() >= 0.0
        assert result_df['reflectance'].max() <= 1.0

    def test_values_above_one_clipped(self):
        """Test that values above 1 are clipped to 1."""
        df = pd.DataFrame({
            'reflectance': [0.0, 0.5, 1.1, 2.0, 10.5]
        })
        result_df, count = validate_reflectance_range(df, column='reflectance')
        
        assert count == 3, "Should detect 3 values above 1."
        assert result_df['reflectance'].iloc[2] == 1.0, "Value 1.1 should be clipped to 1."
        assert result_df['reflectance'].iloc[3] == 1.0, "Value 2.0 should be clipped to 1."
        assert result_df['reflectance'].iloc[4] == 1.0, "Value 10.5 should be clipped to 1."
        
        # Assert final range
        assert result_df['reflectance'].min() >= 0.0
        assert result_df['reflectance'].max() <= 1.0

    def test_mixed_out_of_range_clipped(self):
        """Test mixed negative and positive out-of-range values."""
        df = pd.DataFrame({
            'reflectance': [-1.0, 0.5, 1.5, -0.2, 0.8, 2.5]
        })
        result_df, count = validate_reflectance_range(df, column='reflectance')
        
        assert count == 4, "Should detect 4 values out of range."
        
        expected = [0.0, 0.5, 1.0, 0.0, 0.8, 1.0]
        assert result_df['reflectance'].tolist() == expected, "Values should be clipped correctly."

    def test_assertion_on_final_range(self):
        """
        T011b Requirement: Assert that the resulting column is strictly within [0, 1].
        This test verifies the internal assertion logic of the function.
        """
        df = pd.DataFrame({
            'reflectance': [-5.0, 10.0, 0.0, 1.0]
        })
        # This function should raise an AssertionError if clipping fails (which it shouldn't)
        # or if the input is somehow not clippable (e.g. non-numeric).
        result_df, _ = validate_reflectance_range(df, column='reflectance')
        
        # Explicitly check the condition that the function asserts internally
        assert result_df['reflectance'].min() >= 0.0, "Min value must be >= 0"
        assert result_df['reflectance'].max() <= 1.0, "Max value must be <= 1"

    def test_column_not_found_raises_error(self):
        """Test that a ValueError is raised if the column does not exist."""
        df = pd.DataFrame({'other_col': [0.5]})
        with pytest.raises(ValueError):
            validate_reflectance_range(df, column='reflectance')

class TestApplyAtmosphericCorrection:
    """
    Basic sanity test for the correction step to ensure it produces a column.
    """
    def test_correction_creates_reflectance_column(self):
        df = pd.DataFrame({'DN': [100, 200, 300]})
        result = apply_atmospheric_correction(df)
        assert 'reflectance' in result.columns
        
    def test_correction_may_produce_out_of_range(self):
        """
        Verify that the correction step (as implemented in preprocess.py) 
        can produce values outside [0, 1] to justify the need for T011b validation.
        """
        # With DN=100, (100-100)/500 = 0.0
        # With DN=0, (0-100)/500 = -0.2 (out of range)
        # With DN=1000, (1000-100)/500 = 1.8 (out of range)
        df = pd.DataFrame({'DN': [0, 100, 1000]})
        result = apply_atmospheric_correction(df)
        
        assert result['reflectance'].iloc[0] < 0.0, "Correction should produce negative value for low DN."
        assert result['reflectance'].iloc[2] > 1.0, "Correction should produce value > 1 for high DN."