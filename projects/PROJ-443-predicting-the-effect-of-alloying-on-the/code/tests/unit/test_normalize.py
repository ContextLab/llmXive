"""
Unit tests for the normalization module.

Tests cover:
- Composition column identification
- Single row normalization
- DataFrame normalization
- Edge cases (NaN, zero sum, already normalized)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.normalize import (
    get_composition_columns,
    normalize_composition_row,
    normalize_dataframe
)


class TestGetCompositionColumns:
    """Tests for identifying composition columns."""

    def test_explicit_element_columns(self):
        """Test with explicit element column names."""
        df = pd.DataFrame({
            'Fe': [0.3, 0.2],
            'Ni': [0.3, 0.2],
            'Cr': [0.3, 0.2],
            'Co': [0.1, 0.2],
            'other': [1, 2]
        })
        cols = get_composition_columns(df)
        assert 'Fe' in cols
        assert 'Ni' in cols
        assert 'Cr' in cols
        assert 'Co' in cols
        assert 'other' not in cols

    def test_element_suffix_columns(self):
        """Test with columns containing 'element' in the name."""
        df = pd.DataFrame({
            'element_Fe': [0.3, 0.2],
            'element_Ni': [0.3, 0.2],
            'other': [1, 2]
        })
        cols = get_composition_columns(df)
        assert 'element_Fe' in cols
        assert 'element_Ni' in cols
        assert 'other' not in cols

    def test_no_composition_columns(self):
        """Test with no composition columns."""
        df = pd.DataFrame({
            'A': [1, 2],
            'B': [3, 4],
            'C': [5, 6]
        })
        cols = get_composition_columns(df)
        # Should fallback to numeric columns or return empty
        assert isinstance(cols, list)


class TestNormalizeCompositionRow:
    """Tests for single row normalization."""

    def test_normalize_non_normalized_row(self):
        """Test normalizing a row that doesn't sum to 1."""
        row = pd.Series({
            'Fe': 0.3,
            'Ni': 0.3,
            'Cr': 0.3
        })
        composition_cols = ['Fe', 'Ni', 'Cr']

        norm_row, was_adjusted, msg = normalize_composition_row(row, composition_cols)

        assert was_adjusted is True
        assert np.isclose(norm_row['Fe'], 0.333333, atol=1e-5)
        assert np.isclose(norm_row['Ni'], 0.333333, atol=1e-5)
        assert np.isclose(norm_row['Cr'], 0.333333, atol=1e-5)
        assert "Normalized" in msg

    def test_skip_already_normalized_row(self):
        """Test skipping a row that already sums to 1."""
        row = pd.Series({
            'Fe': 0.4,
            'Ni': 0.4,
            'Cr': 0.2
        })
        composition_cols = ['Fe', 'Ni', 'Cr']

        norm_row, was_adjusted, msg = normalize_composition_row(row, composition_cols)

        assert was_adjusted is False
        assert "Already normalized" in msg

    def test_skip_nan_values(self):
        """Test skipping a row with NaN values."""
        row = pd.Series({
            'Fe': np.nan,
            'Ni': 0.5,
            'Cr': 0.5
        })
        composition_cols = ['Fe', 'Ni', 'Cr']

        norm_row, was_adjusted, msg = normalize_composition_row(row, composition_cols)

        assert was_adjusted is False
        assert "Contains NaN" in msg

    def test_skip_zero_sum(self):
        """Test skipping a row with zero sum."""
        row = pd.Series({
            'Fe': 0.0,
            'Ni': 0.0,
            'Cr': 0.0
        })
        composition_cols = ['Fe', 'Ni', 'Cr']

        norm_row, was_adjusted, msg = normalize_composition_row(row, composition_cols)

        assert was_adjusted is False
        assert "Sum is zero" in msg


class TestNormalizeDataFrame:
    """Tests for DataFrame normalization."""

    def test_normalize_dataframe(self):
        """Test normalizing a full DataFrame."""
        df = pd.DataFrame({
            'Fe': [0.3, 0.2, 0.5],
            'Ni': [0.3, 0.2, 0.5],
            'Cr': [0.3, 0.2, 0.0],  # Third row sums to 1.0 already
            'other': [1, 2, 3]
        })

        norm_df, stats = normalize_dataframe(df)

        assert len(norm_df) == len(df)
        assert stats['normalized'] is True
        assert stats['rows_normalized'] >= 1  # At least one row should be normalized

        # Check that normalized rows sum to 1
        composition_cols = ['Fe', 'Ni', 'Cr']
        row_sums = norm_df[composition_cols].sum(axis=1)
        # Allow for floating point tolerance
        assert np.allclose(row_sums, 1.0, atol=1e-6)

    def test_dataframe_with_all_nan(self):
        """Test DataFrame where all rows have NaN."""
        df = pd.DataFrame({
            'Fe': [np.nan, np.nan],
            'Ni': [np.nan, np.nan],
            'Cr': [np.nan, np.nan]
        })

        norm_df, stats = normalize_dataframe(df)

        assert stats['rows_normalized'] == 0
        assert stats['rows_skipped'] == 2

    def test_dataframe_with_zero_sums(self):
        """Test DataFrame where all rows sum to zero."""
        df = pd.DataFrame({
            'Fe': [0.0, 0.0],
            'Ni': [0.0, 0.0],
            'Cr': [0.0, 0.0]
        })

        norm_df, stats = normalize_dataframe(df)

        assert stats['rows_normalized'] == 0
        assert stats['rows_skipped'] == 2


class TestNormalizationEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_element(self):
        """Test with a single element composition."""
        df = pd.DataFrame({
            'Fe': [1.0, 0.5],
            'other': [1, 2]
        })

        norm_df, stats = normalize_dataframe(df)

        # First row should remain 1.0, second should stay 0.5 (sum=0.5, normalized=1.0)
        composition_cols = ['Fe']
        assert np.isclose(norm_df.loc[0, 'Fe'], 1.0)
        assert np.isclose(norm_df.loc[1, 'Fe'], 1.0)  # 0.5/0.5 = 1.0

    def test_very_small_values(self):
        """Test with very small composition values."""
        df = pd.DataFrame({
            'Fe': [1e-10, 1e-20],
            'Ni': [1e-10, 1e-20],
            'Cr': [1e-10, 1e-20]
        })

        norm_df, stats = normalize_dataframe(df)

        # Should normalize correctly even with small values
        composition_cols = ['Fe', 'Ni', 'Cr']
        row_sums = norm_df[composition_cols].sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)

    def test_large_dataframe(self):
        """Test with a larger DataFrame for performance."""
        np.random.seed(42)
        n_rows = 1000
        df = pd.DataFrame({
            'Fe': np.random.rand(n_rows),
            'Ni': np.random.rand(n_rows),
            'Cr': np.random.rand(n_rows),
            'Co': np.random.rand(n_rows)
        })

        norm_df, stats = normalize_dataframe(df)

        assert len(norm_df) == n_rows
        composition_cols = ['Fe', 'Ni', 'Cr', 'Co']
        row_sums = norm_df[composition_cols].sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)