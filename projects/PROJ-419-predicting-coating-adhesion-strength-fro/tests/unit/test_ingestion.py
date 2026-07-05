import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.ingestion import exclude_missing_surface_roughness

class TestExcludeMissingSurfaceRoughness:
    """Tests for T027: Exclude records with missing surface roughness data."""

    def setup_method(self):
        """Setup test data."""
        self.data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'RMS_Roughness': [0.5, np.nan, 0.8, 0.9, np.nan],
            'Ra': [0.2, 0.3, np.nan, 0.4, 0.5],
            'adhesion_strength': [10.0, 12.0, 11.0, 13.0, 14.0]
        })

    def test_exclude_strategy_removes_missing(self):
        """Test that 'exclude' strategy removes rows with any missing roughness data."""
        result = exclude_missing_surface_roughness(self.data, strategy='exclude')
        
        # Expected: rows 0, 3 (ids 1 and 4) remain. Rows 1, 2, 4 (ids 2, 3, 5) removed.
        # Row 1: RMS_Roughness is NaN
        # Row 2: Ra is NaN
        # Row 4: RMS_Roughness is NaN
        expected_len = 2
        assert len(result) == expected_len
        assert list(result['id']) == [1, 4]
        assert result['RMS_Roughness'].isna().sum() == 0
        assert result['Ra'].isna().sum() == 0

    def test_impute_median_strategy_fills_missing(self):
        """Test that 'impute_median' strategy fills missing values with column median."""
        result = exclude_missing_surface_roughness(self.data, strategy='impute_median')
        
        # Expected: all rows remain, but NaNs are filled.
        # RMS_Roughness non-NaN values: 0.5, 0.8, 0.9 -> Median = 0.8
        # Ra non-NaN values: 0.2, 0.3, 0.4, 0.5 -> Median = 0.35
        
        assert len(result) == 5
        assert result['RMS_Roughness'].isna().sum() == 0
        assert result['Ra'].isna().sum() == 0
        
        # Check specific imputed values
        # Row 1 (id 2): RMS_Roughness was NaN, should be 0.8
        assert result.loc[result['id'] == 2, 'RMS_Roughness'].values[0] == 0.8
        # Row 2 (id 3): Ra was NaN, should be 0.35
        assert result.loc[result['id'] == 3, 'Ra'].values[0] == 0.35

    def test_no_missing_data_unchanged(self):
        """Test that data without missing values is returned unchanged."""
        clean_data = pd.DataFrame({
            'id': [1, 2],
            'RMS_Roughness': [0.5, 0.8],
            'adhesion_strength': [10.0, 12.0]
        })
        
        result = exclude_missing_surface_roughness(clean_data, strategy='exclude')
        pd.testing.assert_frame_equal(result, clean_data)

    def test_invalid_strategy_raises_error(self):
        """Test that an invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            exclude_missing_surface_roughness(self.data, strategy='invalid_strategy')

    def test_no_roughness_columns_skips(self):
        """Test that if no roughness columns exist, the function returns the original dataframe."""
        no_roughness_data = pd.DataFrame({
            'id': [1, 2],
            'composition': ['A', 'B'],
            'adhesion_strength': [10.0, 12.0]
        })
        
        result = exclude_missing_surface_roughness(no_roughness_data, strategy='exclude')
        pd.testing.assert_frame_equal(result, no_roughness_data)
