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
