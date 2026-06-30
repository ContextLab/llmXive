import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports if running standalone, though typically handled by pytest config
# The project structure implies imports from code.src or similar, but the API surface shows
# code/tests/... imports from code.src. Let's assume standard path setup.
# Based on API surface: code/tests/unit/test_preprocessing imports from code.src.utils.constants
# So we assume the test runner is configured to include 'code' in sys.path.

def filter_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where critical data (Tc or impurities) is missing.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with rows containing missing Tc or impurities removed.
    """
    if df.empty:
        return df
    
    # Check for Tc column
    if 'Tc' not in df.columns:
        raise ValueError("DataFrame must contain 'Tc' column")
    
    # Check for impurities column (could be 'impurities_atomic_pct' or similar)
    # Based on T009, the column is 'impurities_atomic_pct'
    impurity_cols = [col for col in df.columns if 'impurity' in col.lower()]
    if not impurity_cols:
        raise ValueError("DataFrame must contain at least one impurity column")
    
    # Drop rows where Tc is null
    df_clean = df.dropna(subset=['Tc'])
    
    # Drop rows where any impurity column is null
    df_clean = df_clean.dropna(subset=impurity_cols)
    
    return df_clean


class TestDataFiltering:
    """Unit tests for data filtering logic in ingestion."""

    def test_drop_rows_with_missing_tc(self):
        """Verify rows with missing Tc are dropped."""
        data = {
            'material': ['MgB2', 'MgB2:Al', 'MgB2:C'],
            'Tc': [39.0, np.nan, 35.0],
            'impurities_atomic_pct': [0.0, 1.0, 2.0]
        }
        df = pd.DataFrame(data)
        result = filter_missing_data(df)
        
        assert len(result) == 2
        assert result['Tc'].isna().sum() == 0
        assert 'MgB2:Al' not in result['material'].values

    def test_drop_rows_with_missing_impurities(self):
        """Verify rows with missing impurities are dropped."""
        data = {
            'material': ['MgB2', 'MgB2:Al', 'MgB2:C'],
            'Tc': [39.0, 38.0, 35.0],
            'impurities_atomic_pct': [0.0, np.nan, 2.0]
        }
        df = pd.DataFrame(data)
        result = filter_missing_data(df)
        
        assert len(result) == 2
        assert 'MgB2:Al' not in result['material'].values

    def test_drop_rows_with_both_missing(self):
        """Verify rows with both Tc and impurities missing are dropped."""
        data = {
            'material': ['MgB2', 'MgB2:Al', 'MgB2:C'],
            'Tc': [39.0, np.nan, np.nan],
            'impurities_atomic_pct': [0.0, np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        result = filter_missing_data(df)
        
        assert len(result) == 1
        assert result.iloc[0]['material'] == 'MgB2'

    def test_empty_dataframe(self):
        """Verify empty dataframe is handled correctly."""
        df = pd.DataFrame(columns=['material', 'Tc', 'impurities_atomic_pct'])
        result = filter_missing_data(df)
        
        assert result.empty

    def test_no_missing_data(self):
        """Verify dataframe with no missing data is returned unchanged."""
        data = {
            'material': ['MgB2', 'MgB2:Al', 'MgB2:C'],
            'Tc': [39.0, 38.0, 35.0],
            'impurities_atomic_pct': [0.0, 1.0, 2.0]
        }
        df = pd.DataFrame(data)
        result = filter_missing_data(df)
        
        assert len(result) == 3
        pd.testing.assert_frame_equal(result, df)

    def test_multiple_impurity_columns(self):
        """Verify rows with missing values in any impurity column are dropped."""
        data = {
            'material': ['MgB2', 'MgB2:Al', 'MgB2:C', 'MgB2:Fe'],
            'Tc': [39.0, 38.0, 35.0, 32.0],
            'impurities_atomic_pct': [0.0, 1.0, np.nan, 3.0],
            'other_impurity_pct': [0.0, np.nan, 2.0, 4.0]
        }
        df = pd.DataFrame(data)
        result = filter_missing_data(df)
        
        # Should drop MgB2:C (missing impurities_atomic_pct) and MgB2:Al (missing other_impurity_pct)
        assert len(result) == 2
        assert 'MgB2:Al' not in result['material'].values
        assert 'MgB2:C' not in result['material'].values

    def test_raises_error_without_tc_column(self):
        """Verify error is raised if Tc column is missing."""
        data = {
            'material': ['MgB2', 'MgB2:Al'],
            'impurities_atomic_pct': [0.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="DataFrame must contain 'Tc' column"):
            filter_missing_data(df)

    def test_raises_error_without_impurity_column(self):
        """Verify error is raised if no impurity column is found."""
        data = {
            'material': ['MgB2', 'MgB2:Al'],
            'Tc': [39.0, 38.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="DataFrame must contain at least one impurity column"):
            filter_missing_data(df)