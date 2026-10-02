import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch, MagicMock

# Add code to path for imports
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.src.ingestion.preprocess import filter_valid_entries
from code.src.ingestion.download_supercon import validate_impurity_coverage

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


class TestSuperConImpurityValidation:
    """Unit tests for SuperCon impurity validation logic."""

    def test_valid_impurity_coverage(self):
        """Verify validation passes when >= 50% entries have impurity data."""
        # Create dataset with 60% valid impurity entries
        data = {
            'material': ['MgB2'] * 5 + ['MgB2:Al'] * 5,
            'Tc': [39.0] * 10,
            'impurity_element': [None, None, None, None, None, 'Al', 'Al', 'Al', 'Al', 'Al']
        }
        df = pd.DataFrame(data)
        
        # Should not raise
        result = validate_impurity_coverage(df)
        assert result is True

    def test_invalid_impurity_coverage_low(self):
        """Verify validation fails when < 50% entries have impurity data."""
        # Create dataset with only 40% valid impurity entries
        data = {
            'material': ['MgB2'] * 6 + ['MgB2:Al'] * 4,
            'Tc': [39.0] * 10,
            'impurity_element': [None] * 6 + ['Al'] * 4
        }
        df = pd.DataFrame(data)
        
        # Should raise SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            validate_impurity_coverage(df)
        
        assert exc_info.value.code == 1

    def test_invalid_impurity_coverage_very_low(self):
        """Verify validation fails when almost no entries have impurity data."""
        # Create dataset with only 10% valid impurity entries
        data = {
            'material': ['MgB2'] * 9 + ['MgB2:Al'],
            'Tc': [39.0] * 10,
            'impurity_element': [None] * 9 + ['Al']
        }
        df = pd.DataFrame(data)
        
        # Should raise SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            validate_impurity_coverage(df)
        
        assert exc_info.value.code == 1

    def test_no_impurity_columns(self):
        """Verify validation fails when no impurity columns exist."""
        data = {
            'material': ['MgB2', 'MgB2:Al'],
            'Tc': [39.0, 38.0]
        }
        df = pd.DataFrame(data)
        
        # Should raise SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            validate_impurity_coverage(df)
        
        assert exc_info.value.code == 1

    def test_empty_dataframe(self):
        """Verify validation fails for empty dataframe."""
        df = pd.DataFrame(columns=['material', 'Tc', 'impurity_element'])
        
        # Should raise SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            validate_impurity_coverage(df)
        
        assert exc_info.value.code == 1

    def test_exact_50_percent_coverage(self):
        """Verify validation passes at exactly 50% coverage."""
        # Create dataset with exactly 50% valid impurity entries
        data = {
            'material': ['MgB2'] * 5 + ['MgB2:Al'] * 5,
            'Tc': [39.0] * 10,
            'impurity_element': [None] * 5 + ['Al'] * 5
        }
        df = pd.DataFrame(data)
        
        # Should not raise (50% meets threshold)
        result = validate_impurity_coverage(df)
        assert result is True

    def test_multiple_impurity_columns_partial_valid(self):
        """Verify validation with multiple impurity columns where some rows have partial data."""
        data = {
            'material': ['MgB2'] * 4 + ['MgB2:Al'] * 3 + ['MgB2:C'] * 3,
            'Tc': [39.0] * 10,
            'impurity_element': [None, None, None, None, 'Al', 'Al', 'Al', None, None, None],
            'doping_element': [None, None, None, None, None, None, None, 'C', 'C', 'C']
        }
        df = pd.DataFrame(data)
        
        # 7 out of 10 rows have at least one impurity value = 70%
        # Should pass
        result = validate_impurity_coverage(df)
        assert result is True

    def test_script_exits_with_code_1_on_low_coverage(self):
        """Verify the script exits with code 1 when validation fails."""
        # This test mocks the dataset loading to return a low-coverage dataset
        with patch('code.src.ingestion.download_supercon.load_dataset') as mock_load:
            # Create a mock dataset iterator that yields low-coverage data
            mock_data = [
                {'material': 'MgB2', 'Tc': 39.0, 'impurity_element': None},
                {'material': 'MgB2', 'Tc': 39.0, 'impurity_element': None},
                {'material': 'MgB2', 'Tc': 39.0, 'impurity_element': None},
                {'material': 'MgB2', 'Tc': 39.0, 'impurity_element': None},
                {'material': 'MgB2', 'Tc': 39.0, 'impurity_element': None},
                {'material': 'MgB2:Al', 'Tc': 38.0, 'impurity_element': 'Al'},
            ]
            
            mock_load.return_value.__iter__ = lambda self: iter(mock_data)
            mock_load.return_value.__getitem__ = lambda self, key: mock_data[key]
            
            # Run the script
            result = subprocess.run(
                [sys.executable, '-m', 'code.src.ingestion.download_supercon'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parent.parent.parent
            )
            
            # Should exit with code 1
            assert result.returncode == 1
            assert 'below threshold' in result.stderr.lower() or 'below threshold' in result.stdout.lower()