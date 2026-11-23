import pandas as pd
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import validate_no_missing_predictors

class TestValidateNoMissingPredictors:
    
    def test_no_missing_values_passes(self):
        """Test that a dataframe with no missing values in predictors passes."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.0, 1.2, 1.1],
            'electronegativity_std': [0.5, 0.6, 0.4],
            'valence_electron_concentration': [2.0, 2.1, 1.9],
            'cation_size_variance': [0.1, 0.2, 0.15],
            'sintering_temp': [1000, 1100, 1050],
            'primary_anion_cation_group': ['Group A', 'Group B', 'Group A'],
            'other_col': [1, 2, 3]
        })
        
        # Should not raise
        result = validate_no_missing_predictors(df)
        assert result is not None
        assert len(result) == 3

    def test_missing_values_raises_error(self):
        """Test that a dataframe with missing values in predictors raises ValueError."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.0, None, 1.1],
            'electronegativity_std': [0.5, 0.6, 0.4],
            'valence_electron_concentration': [2.0, 2.1, 1.9],
            'cation_size_variance': [0.1, 0.2, 0.15],
            'sintering_temp': [1000, 1100, 1050],
            'primary_anion_cation_group': ['Group A', 'Group B', 'Group A'],
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_no_missing_predictors(df)
        
        assert "Missing values found in primary predictor" in str(exc_info.value)
        assert "Validation Failed" in str(exc_info.value)

    def test_missing_column_raises_error(self):
        """Test that a dataframe missing a required predictor column raises ValueError."""
        df = pd.DataFrame({
            'mean_atomic_radius': [1.0, 1.2, 1.1],
            'electronegativity_std': [0.5, 0.6, 0.4],
            'valence_electron_concentration': [2.0, 2.1, 1.9],
            # Missing 'cation_size_variance', 'sintering_temp', etc.
            'primary_anion_cation_group': ['Group A', 'Group B', 'Group A'],
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_no_missing_predictors(df)
        
        assert "not found in dataset" in str(exc_info.value) or "Validation Failed" in str(exc_info.value)

    def test_all_nan_column_raises_error(self):
        """Test that a dataframe with a column full of NaNs raises error."""
        df = pd.DataFrame({
            'mean_atomic_radius': [None, None, None],
            'electronegativity_std': [0.5, 0.6, 0.4],
            'valence_electron_concentration': [2.0, 2.1, 1.9],
            'cation_size_variance': [0.1, 0.2, 0.15],
            'sintering_temp': [1000, 1100, 1050],
            'primary_anion_cation_group': ['Group A', 'Group B', 'Group A'],
        })
        
        with pytest.raises(ValueError):
            validate_no_missing_predictors(df)
