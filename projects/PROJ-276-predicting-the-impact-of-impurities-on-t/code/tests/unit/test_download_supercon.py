"""
Unit tests for download_supercon.py logic.

Specifically tests the validation logic that exits if >50% of entries
lack impurity columns.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion.download_supercon import validate_impurity_coverage, MAX_NULL_RATIO

class TestImpurityValidation:
    """Tests for impurity data coverage validation."""

    def test_perfect_coverage(self):
        """100% of rows have impurity data -> valid."""
        data = {
            'material': ['MgB2', 'MgB2:Al', 'MgB2:C'],
            'Tc': [39.0, 38.0, 35.0],
            'impurity_wt_pct': [0.0, 1.0, 2.0]
        }
        df = pd.DataFrame(data)
        ratio = validate_impurity_coverage(df)
        assert ratio == 1.0

    def test_partial_coverage_below_threshold(self):
        """40% nulls (60% valid) -> valid (ratio > 0.5)."""
        # 5 rows, 2 nulls -> 3 valid -> 60%
        data = {
            'material': ['A', 'B', 'C', 'D', 'E'],
            'Tc': [39.0, 38.0, 35.0, 32.0, 30.0],
            'impurity_wt_pct': [1.0, np.nan, 2.0, np.nan, 3.0]
        }
        df = pd.DataFrame(data)
        ratio = validate_impurity_coverage(df)
        assert ratio == 0.6
        assert (1.0 - ratio) <= MAX_NULL_RATIO

    def test_partial_coverage_above_threshold(self):
        """60% nulls (40% valid) -> invalid (ratio < 0.5)."""
        # 5 rows, 3 nulls -> 2 valid -> 40%
        data = {
            'material': ['A', 'B', 'C', 'D', 'E'],
            'Tc': [39.0, 38.0, 35.0, 32.0, 30.0],
            'impurity_wt_pct': [1.0, np.nan, np.nan, np.nan, 3.0]
        }
        df = pd.DataFrame(data)
        ratio = validate_impurity_coverage(df)
        assert ratio == 0.4
        assert (1.0 - ratio) > MAX_NULL_RATIO

    def test_no_impurity_columns(self):
        """No impurity columns found -> 0% coverage."""
        data = {
            'material': ['A', 'B'],
            'Tc': [39.0, 38.0]
        }
        df = pd.DataFrame(data)
        ratio = validate_impurity_coverage(df)
        assert ratio == 0.0

    def test_empty_dataframe(self):
        """Empty dataframe -> 0% coverage."""
        df = pd.DataFrame(columns=['material', 'Tc', 'impurity_wt_pct'])
        ratio = validate_impurity_coverage(df)
        assert ratio == 0.0

    def test_multiple_impurity_columns_any_valid(self):
        """Multiple impurity columns: row valid if ANY column has data."""
        data = {
            'material': ['A', 'B', 'C'],
            'Tc': [39.0, 38.0, 35.0],
            'impurity_wt_pct': [1.0, np.nan, np.nan],
            'dopant_at_pct': [np.nan, 2.0, np.nan]
        }
        df = pd.DataFrame(data)
        # Row A: has wt%
        # Row B: has at%
        # Row C: has neither
        # 2/3 valid -> 66.6%
        ratio = validate_impurity_coverage(df)
        assert abs(ratio - 0.666666) < 0.01

class TestMainExecutionFailure:
    """Tests for the main function's exit behavior on bad data."""

    def test_main_exits_on_high_null_ratio(self):
        """Mock load to return bad data, verify sys.exit(1) is called."""
        bad_data = {
            'material': ['A', 'B', 'C', 'D', 'E'],
            'Tc': [39.0, 38.0, 35.0, 32.0, 30.0],
            'impurity_wt_pct': [1.0, np.nan, np.nan, np.nan, np.nan]
        }
        df_bad = pd.DataFrame(bad_data)
        
        with patch('src.ingestion.download_supercon.load_dataset') as mock_load:
            # Mock the dataset object
            mock_ds = MagicMock()
            mock_ds.to_pandas.return_value = df_bad
            mock_load.return_value = mock_ds
            
            with patch('sys.exit') as mock_exit:
                from src.ingestion.download_supercon import main
                main()
                # Verify exit was called with code 1
                mock_exit.assert_called_once_with(1)

    def test_main_succeeds_on_good_data(self):
        """Mock load to return good data, verify sys.exit(0) is called."""
        good_data = {
            'material': ['A', 'B', 'C'],
            'Tc': [39.0, 38.0, 35.0],
            'impurity_wt_pct': [1.0, 2.0, 3.0]
        }
        df_good = pd.DataFrame(good_data)
        
        with patch('src.ingestion.download_supercon.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_ds.to_pandas.return_value = df_good
            mock_load.return_value = mock_ds
            
            with patch('sys.exit') as mock_exit:
                from src.ingestion.download_supercon import main
                main()
                mock_exit.assert_called_once_with(0)
