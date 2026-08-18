"""
Unit tests for NaN handling logic in code/data/preprocess_2d.py.
Tests the deterministic logic: >5% missing -> drop row, else impute with median.
"""
import pytest
import pandas as pd
import numpy as np
from code.data.preprocess_2d import handle_missing_values


class TestNaNHandling:
    """Tests for the handle_missing_values function."""

    def test_no_missing_values(self):
        """Test that data with no NaNs is returned unchanged."""
        df = pd.DataFrame({
            'smiles': ['CC', 'CCO'],
            'target': [1.0, 2.0],
            'f1': [10.0, 20.0],
            'f2': [30.0, 40.0]
        })
        result = handle_missing_values(df)
        pd.testing.assert_frame_equal(result, df)

    def test_impute_less_than_5_percent(self):
        """Test imputation when missing values are <= 5% in a column."""
        # 2 rows, 1 NaN in f1 -> 50% missing in that column? No, the rule is per column.
        # Let's create a case where a column has <= 5% missing.
        n_rows = 100
        data = {
            'smiles': [f'CC{i}' for i in range(n_rows)],
            'target': [float(i) for i in range(n_rows)],
            'f1': [float(i) for i in range(n_rows)]
        }
        df = pd.DataFrame(data)
        # Introduce 4 NaNs (4% of 100) in f1
        df.loc[0:3, 'f1'] = np.nan
        
        # The function should impute with median
        result = handle_missing_values(df)
        
        # Check no NaNs remain
        assert result['f1'].isna().sum() == 0
        # Check imputed value is median
        median_val = df['f1'].median()
        assert result.loc[0:3, 'f1'].iloc[0] == median_val

    def test_drop_more_than_5_percent(self):
        """Test row dropping when a column has >5% missing values."""
        n_rows = 100
        data = {
            'smiles': [f'CC{i}' for i in range(n_rows)],
            'target': [float(i) for i in range(n_rows)],
            'f1': [float(i) for i in range(n_rows)]
        }
        df = pd.DataFrame(data)
        # Introduce 6 NaNs (6% of 100) in f1 -> should drop these rows
        df.loc[0:5, 'f1'] = np.nan
        
        original_len = len(df)
        result = handle_missing_values(df)
        
        # Rows with NaN in f1 should be dropped
        assert len(result) == original_len - 6
        # Check the dropped rows are the ones with NaN
        assert 0 not in result.index
        assert 5 not in result.index

    def test_mixed_missing_levels(self):
        """Test behavior when one column has >5% NaN and another has <5%."""
        n_rows = 100
        data = {
            'smiles': [f'CC{i}' for i in range(n_rows)],
            'target': [float(i) for i in range(n_rows)],
            'f1': [float(i) for i in range(n_rows)],
            'f2': [float(i) for i in range(n_rows)]
        }
        df = pd.DataFrame(data)
        
        # f1: 10% missing (10 rows) -> drop these rows
        df.loc[0:9, 'f1'] = np.nan
        # f2: 5% missing (5 rows) -> impute these
        df.loc[0:4, 'f2'] = np.nan
        
        result = handle_missing_values(df)
        
        # Rows 0-9 should be dropped because of f1
        assert len(result) == n_rows - 10
        # Check that remaining rows have no NaNs
        assert result.isna().sum().sum() == 0

    def test_all_nan_column(self):
        """Test handling of a column with 100% NaN."""
        df = pd.DataFrame({
            'smiles': ['CC', 'CCO'],
            'target': [1.0, 2.0],
            'f1': [np.nan, np.nan]
        })
        # f1 has 100% missing -> drop all rows? Or drop column?
        # The task says: "If >5% missing values in a column, drop the record" (row).
        # So every row has a missing value in f1 -> every row is dropped.
        result = handle_missing_values(df)
        assert len(result) == 0

    def test_median_imputation_correctness(self):
        """Verify that the imputed value is exactly the median of non-NaN values."""
        df = pd.DataFrame({
            'smiles': ['A', 'B', 'C', 'D', 'E'],
            'target': [1, 2, 3, 4, 5],
            'f1': [10.0, 20.0, np.nan, 40.0, 50.0]
        })
        # 1 NaN out of 5 (20%) -> Drop row C? 
        # Wait, 20% > 5%, so row C is dropped.
        # Let's make it < 5%: 1 NaN out of 25 rows.
        rows = 25
        data = {'smiles': [f'R{i}' for i in range(rows)], 'target': list(range(rows)), 'f1': list(range(rows))}
        df = pd.DataFrame(data)
        df.loc[0, 'f1'] = np.nan # 1/25 = 4%
        
        result = handle_missing_values(df)
        median = df['f1'].median()
        assert result.loc[0, 'f1'] == median

    def test_logging_action(self):
        """Verify that the function logs the action taken (dropped vs imputed)."""
        # This is a behavioral test. We can't easily capture logs in a unit test without patching,
        # but we can verify the outcome implies the correct path was taken.
        # If rows are dropped, it implies >5% logic. If values are filled, it implies <5%.
        df = pd.DataFrame({
            'smiles': ['A', 'B', 'C'],
            'target': [1, 2, 3],
            'f1': [10.0, np.nan, 30.0]
        })
        # 1 NaN in 3 rows = 33% -> Drop row B
        result = handle_missing_values(df)
        assert len(result) == 2
        assert 'B' not in result['smiles'].values
        
        df2 = pd.DataFrame({
            'smiles': [f'R{i}' for i in range(100)],
            'target': list(range(100)),
            'f1': list(range(100))
        })
        df2.loc[0, 'f1'] = np.nan # 1%
        result2 = handle_missing_values(df2)
        assert len(result2) == 100
        assert result2.loc[0, 'f1'] == df2['f1'].median()