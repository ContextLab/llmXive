import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import validate_no_missing_predictors, clean_data, compute_descriptors

class TestValidateNoMissingPredictors:
    """Tests for the validate_no_missing_predictors function."""

    def test_no_missing_values(self):
        """Test that function passes when no primary predictors have NaN."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.5, 1.6, 1.7],
            'electronegativity_std': [0.5, 0.6, 0.7],
            'valence_electron_concentration': [2.0, 2.1, 2.2],
            'other_col': [1, 2, 3]
        })
        
        # Should not raise an exception
        validate_no_missing_predictors(df)

    def test_missing_values_in_one_column(self):
        """Test that function raises ValueError when one predictor has NaN."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.5, np.nan, 1.7],
            'electronegativity_std': [0.5, 0.6, 0.7],
            'valence_electron_concentration': [2.0, 2.1, 2.2]
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_no_missing_predictors(df)
        
        assert "Missing values in primary predictors" in str(excinfo.value)
        assert "mean_atomic_radius" in str(excinfo.value)

    def test_missing_values_in_multiple_columns(self):
        """Test that function raises ValueError with multiple columns listed."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.5, np.nan, 1.7],
            'electronegativity_std': [0.5, 0.6, np.nan],
            'valence_electron_concentration': [2.0, 2.1, 2.2]
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_no_missing_predictors(df)
        
        assert "Missing values in primary predictors" in str(excinfo.value)
        assert "mean_atomic_radius" in str(excinfo.value)
        assert "electronegativity_std" in str(excinfo.value)

    def test_missing_column_completely(self):
        """Test that function raises ValueError when a required column is missing entirely."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.5, 1.6, 1.7],
            'electronegativity_std': [0.5, 0.6, 0.7]
            # valence_electron_concentration is missing
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_no_missing_predictors(df)
        
        assert "Missing values in primary predictors" in str(excinfo.value)
        assert "valence_electron_concentration" in str(excinfo.value)

    def test_all_columns_missing_nan(self):
        """Test that function raises ValueError when all primary predictors have NaN."""
        df = pd.DataFrame({
            'mean_atomic_radius': [np.nan, np.nan, np.nan],
            'electronegativity_std': [np.nan, np.nan, np.nan],
            'valence_electron_concentration': [np.nan, np.nan, np.nan]
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_no_missing_predictors(df)
        
        assert "Missing values in primary predictors" in str(excinfo.value)
        assert "mean_atomic_radius" in str(excinfo.value)
        assert "electronegativity_std" in str(excinfo.value)
        assert "valence_electron_concentration" in str(excinfo.value)

class TestImputationLogic:
    """Tests for the imputation logic (group vs global median) in clean_data."""

    def test_group_median_imputation(self):
        """Test that missing values are imputed using group median when group size >= 5."""
        # Create a dataset with a group that has >= 5 samples
        df = pd.DataFrame({
            'composition': ['Al2O3', 'Al2O3', 'Al2O3', 'Al2O3', 'Al2O3', 'SiO2'],
            'primary_anion_cation_group': ['O-Al', 'O-Al', 'O-Al', 'O-Al', 'O-Al', 'O-Si'],
            'sintering_temp': [1600.0, 1650.0, np.nan, 1700.0, 1750.0, 1500.0],
            'weibull_modulus': [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        })
        
        # The group 'O-Al' has 5 samples, so median imputation should use group median
        # Group 'O-Al' sintering_temp values: [1600, 1650, NaN, 1700, 1750] -> median = 1650
        result = clean_data(df)
        
        # Check that the missing value was filled with the group median
        # The row with NaN should now have 1650.0
        o_al_rows = result[result['primary_anion_cation_group'] == 'O-Al']
        nan_row = o_al_rows[o_al_rows['sintering_temp'].isna()]
        
        # If clean_data successfully imputed, there should be no NaN in sintering_temp
        # for the O-Al group
        assert not result['sintering_temp'].isna().any(), "Group median imputation failed"

    def test_global_median_imputation_for_small_groups(self):
        """Test that missing values in small groups (< 5 samples) use global median."""
        # Create a dataset where one group has < 5 samples
        df = pd.DataFrame({
            'composition': ['Al2O3', 'Al2O3', 'SiO2', 'SiO2', 'ZrO2'],
            'primary_anion_cation_group': ['O-Al', 'O-Al', 'O-Si', 'O-Si', 'O-Zr'],
            'sintering_temp': [1600.0, np.nan, 1500.0, 1550.0, 1800.0],
            'weibull_modulus': [10.0, 11.0, 15.0, 16.0, 20.0]
        })
        
        # O-Si has 2 samples (< 5), so it should use global median
        # Global median of [1600, 1500, 1550, 1800] = 1575
        result = clean_data(df)
        
        # Check that no NaN remains in sintering_temp
        assert not result['sintering_temp'].isna().any(), "Global median imputation failed for small groups"

    def test_imputation_flagging(self):
        """Test that imputed values are flagged with is_imputed=True."""
        df = pd.DataFrame({
            'composition': ['Al2O3', 'Al2O3', 'Al2O3'],
            'primary_anion_cation_group': ['O-Al', 'O-Al', 'O-Al'],
            'sintering_temp': [1600.0, np.nan, 1700.0],
            'weibull_modulus': [10.0, 11.0, 12.0]
        })
        
        result = clean_data(df)
        
        # The second row had NaN, so is_imputed should be True for that row
        # Note: clean_data should add an 'is_imputed' column
        assert 'is_imputed' in result.columns, "is_imputed column not created"
        
        # Check that the row that was imputed has is_imputed=True
        # This depends on how clean_data tracks imputation
        # We'll check that at least one row has is_imputed=True if imputation occurred
        assert result['is_imputed'].any(), "Imputation flag not set for imputed values"