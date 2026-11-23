import pytest
import pandas as pd
import numpy as np
from augment import detect_zero_variance_columns, exclude_zero_variance_samples

class TestZeroVarianceHandling:
    """Tests for zero-variance detection and exclusion logic."""

    def test_detect_zero_variance_columns_empty_df(self):
        """Test detection on empty DataFrame."""
        df = pd.DataFrame()
        result = detect_zero_variance_columns(df)
        assert result == []

    def test_detect_zero_variance_columns_all_constant(self):
        """Test detection when all columns are constant."""
        df = pd.DataFrame({
            'a': [1, 1, 1],
            'b': [2, 2, 2],
            'target': [0, 1, 0]
        })
        result = detect_zero_variance_columns(df)
        assert 'a' in result
        assert 'b' in result
        assert 'target' not in result

    def test_detect_zero_variance_columns_mixed(self):
        """Test detection with mixed variance columns."""
        df = pd.DataFrame({
            'varied': [1, 2, 3, 4, 5],
            'constant': [5, 5, 5, 5, 5],
            'target': [0, 1, 0, 1, 0]
        })
        result = detect_zero_variance_columns(df)
        assert 'constant' in result
        assert 'varied' not in result
        assert 'target' not in result

    def test_exclude_zero_variance_samples_all_valid(self):
        """Test exclusion when all rows have variance."""
        df = pd.DataFrame({
            'f1': [1, 2, 3],
            'f2': [4, 5, 6],
            'target': [0, 1, 0]
        })
        result = exclude_zero_variance_samples(df, 'target')
        assert len(result) == 3

    def test_exclude_zero_variance_samples_with_bad_rows(self):
        """Test exclusion of rows where all features are identical."""
        df = pd.DataFrame({
            'f1': [1, 2, 3, 5],
            'f2': [4, 5, 6, 5],
            'f3': [7, 8, 9, 5],
            'target': [0, 1, 0, 1]
        })
        # Row 3 has f1=f2=f3=5 (zero variance)
        result = exclude_zero_variance_samples(df, 'target')
        assert len(result) == 3
        # The excluded row should not be in the result
        assert 3 not in result.index.values

    def test_exclude_zero_variance_samples_empty_result(self):
        """Test when all rows are bad."""
        df = pd.DataFrame({
            'f1': [1, 1, 1],
            'f2': [1, 1, 1],
            'target': [0, 1, 0]
        })
        result = exclude_zero_variance_samples(df, 'target')
        assert len(result) == 0

    def test_exclude_zero_variance_samples_single_feature(self):
        """Test with only one feature column (always zero variance if constant, but unique check handles it)."""
        df = pd.DataFrame({
            'f1': [1, 2, 3],
            'target': [0, 1, 0]
        })
        # With one feature, nunique > 1 is always true if values differ
        result = exclude_zero_variance_samples(df, 'target')
        assert len(result) == 3

    def test_exclude_zero_variance_samples_non_numeric_ignored(self):
        """Test that non-numeric columns are ignored in variance check."""
        df = pd.DataFrame({
            'f1': [1, 2, 3],
            'cat': ['a', 'b', 'c'],
            'target': [0, 1, 0]
        })
        result = exclude_zero_variance_samples(df, 'target')
        assert len(result) == 3