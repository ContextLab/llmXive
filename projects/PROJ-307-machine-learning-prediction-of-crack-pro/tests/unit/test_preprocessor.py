"""
Unit tests for code/data/preprocessor.py imputation logic.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocessor import impute_missing, clean_data


class TestImputeMissing:
    """Tests for the impute_missing function."""

    def test_impute_missing_default_column_and_value(self):
        """Test imputation of missing values in 'heat_treatment' with default 'Unknown/Not Specified'."""
        data = {
            'da_dN': [1e-6, 2e-6, 3e-6],
            'delta_K': [10.0, 15.0, 20.0],
            'heat_treatment': ['T6', None, 'Annealed']
        }
        df = pd.DataFrame(data)

        result = impute_missing(df)

        # Check that the None was replaced
        assert result['heat_treatment'].iloc[1] == "Unknown/Not Specified"
        assert result['heat_treatment'].iloc[0] == "T6"
        assert result['heat_treatment'].iloc[2] == "Annealed"
        # Ensure no NaNs remain in that column
        assert result['heat_treatment'].isna().sum() == 0

    def test_impute_missing_custom_column(self):
        """Test imputation on a custom column name."""
        data = {
            'feature_A': [1, 2, np.nan],
            'feature_B': ['x', 'y', 'z']
        }
        df = pd.DataFrame(data)

        result = impute_missing(df, col="feature_A", value=-999)

        assert result['feature_A'].iloc[2] == -999
        assert result['feature_A'].iloc[0] == 1
        assert result['feature_A'].iloc[1] == 2

    def test_impute_missing_no_missing_values(self):
        """Test that function handles data with no missing values gracefully."""
        data = {
            'heat_treatment': ['T6', 'T7', 'Annealed']
        }
        df = pd.DataFrame(data)

        result = impute_missing(df)

        # Values should remain unchanged
        assert result['heat_treatment'].tolist() == ['T6', 'T7', 'Annealed']
        assert result['heat_treatment'].isna().sum() == 0

    def test_impute_missing_all_missing(self):
        """Test imputation when all values in the column are missing."""
        data = {
            'heat_treatment': [None, None, np.nan]
        }
        df = pd.DataFrame(data)

        result = impute_missing(df)

        # All should be replaced with the default value
        assert result['heat_treatment'].tolist() == [
            "Unknown/Not Specified",
            "Unknown/Not Specified",
            "Unknown/Not Specified"
        ]

    def test_impute_missing_preserves_other_columns(self):
        """Test that imputation only affects the target column."""
        data = {
            'da_dN': [1e-6, 2e-6, 3e-6],
            'delta_K': [10.0, 15.0, 20.0],
            'heat_treatment': ['T6', None, 'Annealed']
        }
        df = pd.DataFrame(data)

        original_da_dN = df['da_dN'].copy()
        original_delta_K = df['delta_K'].copy()

        result = impute_missing(df)

        # Check other columns are unchanged
        assert result['da_dN'].equals(original_da_dN)
        assert result['delta_K'].equals(original_delta_K)


class TestCleanData:
    """Tests for the clean_data function."""

    def test_clean_data_basic(self):
        """Test that clean_data returns a DataFrame (placeholder logic)."""
        data = {
            'da_dN': [1e-6, 2e-6, 3e-6],
            'delta_K': [10.0, 15.0, 20.0]
        }
        df = pd.DataFrame(data)

        result = clean_data(df)

        # Currently a placeholder, should just return the input
        assert isinstance(result, pd.DataFrame)
        assert result.shape == df.shape

    def test_clean_data_empty_dataframe(self):
        """Test clean_data with an empty DataFrame."""
        df = pd.DataFrame(columns=['da_dN', 'delta_K'])
        result = clean_data(df)
        assert result.shape == (0, 2)