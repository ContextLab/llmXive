"""
Unit tests for the normalization module (src/data/normalize.py).

These tests verify that composition normalization logic correctly enforces
the sum=1.0 constraint and properly logs adjustments.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.normalize import (
    get_composition_columns,
    normalize_composition_row,
    normalize_dataframe,
    NORMALIZATION_TOLERANCE
)


class TestGetCompositionColumns:
    """Tests for get_composition_columns function."""

    def test_basic_detection(self):
        """Test basic detection of composition columns."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'element_Fe': [0.2, 0.25],
            'element_Cr': [0.2, 0.25],
            'element_Ni': [0.2, 0.25],
            'other_col': ['a', 'b']
        })
        
        cols = get_composition_columns(df)
        assert 'element_Fe' in cols
        assert 'element_Cr' in cols
        assert 'element_Ni' in cols
        assert 'sample_id' not in cols
        assert 'other_col' not in cols

    def test_custom_prefix(self):
        """Test detection with custom prefix."""
        df = pd.DataFrame({
            'comp_Fe': [0.2, 0.25],
            'comp_Cr': [0.2, 0.25],
            'sample_id': [1, 2]
        })
        
        cols = get_composition_columns(df, prefix='comp_')
        assert 'comp_Fe' in cols
        assert 'comp_Cr' in cols
        assert len(cols) == 2

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        cols = get_composition_columns(df)
        assert cols == []

    def test_no_composition_columns(self):
        """Test DataFrame with no composition columns."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'bulk_modulus': [100.0, 150.0]
        })
        
        cols = get_composition_columns(df)
        assert cols == []


class TestNormalizeCompositionRow:
    """Tests for normalize_composition_row function."""

    def test_already_normalized(self):
        """Test row that already sums to 1.0."""
        row = pd.Series({
            'element_Fe': 0.25,
            'element_Cr': 0.25,
            'element_Ni': 0.25,
            'element_Mn': 0.25
        })
        
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']
        normalized_row, log = normalize_composition_row(row, composition_cols)
        
        assert np.isclose(normalized_row['element_Fe'], 0.25)
        assert np.isclose(normalized_row['element_Cr'], 0.25)
        assert log['status'] == 'already_normalized'
        assert np.isclose(log['original_sum'], 1.0)

    def test_needs_normalization(self):
        """Test row that needs normalization."""
        row = pd.Series({
            'element_Fe': 0.2,
            'element_Cr': 0.2,
            'element_Ni': 0.2,
            'element_Mn': 0.2  # Sum = 0.8
        })
        
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']
        normalized_row, log = normalize_composition_row(row, composition_cols)
        
        # Should be normalized to 0.25 each
        assert np.isclose(normalized_row['element_Fe'], 0.25)
        assert np.isclose(normalized_row['element_Cr'], 0.25)
        assert np.isclose(normalized_row['element_Ni'], 0.25)
        assert np.isclose(normalized_row['element_Mn'], 0.25)
        assert log['status'] == 'normalized'
        assert np.isclose(log['original_sum'], 0.8)

    def test_zero_sum(self):
        """Test row with zero sum."""
        row = pd.Series({
            'element_Fe': 0.0,
            'element_Cr': 0.0,
            'element_Ni': 0.0,
            'element_Mn': 0.0
        })
        
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']
        normalized_row, log = normalize_composition_row(row, composition_cols)
        
        assert log['status'] == 'invalid'
        assert log['reason'] == 'zero_sum'

    def test_nan_values(self):
        """Test row with NaN values."""
        row = pd.Series({
            'element_Fe': 0.25,
            'element_Cr': np.nan,
            'element_Ni': 0.25,
            'element_Mn': 0.25
        })
        
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']
        normalized_row, log = normalize_composition_row(row, composition_cols)
        
        assert log['status'] == 'invalid'
        assert log['reason'] == 'contains_nan_or_negative'

    def test_negative_values(self):
        """Test row with negative values."""
        row = pd.Series({
            'element_Fe': 0.25,
            'element_Cr': -0.05,
            'element_Ni': 0.25,
            'element_Mn': 0.55
        })
        
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']
        normalized_row, log = normalize_composition_row(row, composition_cols)
        
        assert log['status'] == 'invalid'
        assert log['reason'] == 'contains_nan_or_negative'


class TestNormalizeDataFrame:
    """Tests for normalize_dataframe function."""

    def test_full_normalization(self):
        """Test normalization of a full DataFrame."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'element_Fe': [0.2, 0.25, 0.18],
            'element_Cr': [0.2, 0.25, 0.22],
            'element_Ni': [0.2, 0.25, 0.20],
            'element_Mn': [0.2, 0.25, 0.20],
            'element_Al': [0.2, 0.0, 0.20]
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        # Check sums
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn', 'element_Al']
        sums = normalized_df[composition_cols].sum(axis=1)
        
        assert np.allclose(sums, 1.0, atol=NORMALIZATION_TOLERANCE)
        assert len(logs_df) == 3

    def test_mixed_normalization(self):
        """Test DataFrame with some rows already normalized."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'element_Fe': [0.25, 0.2],
            'element_Cr': [0.25, 0.2],
            'element_Ni': [0.25, 0.2],
            'element_Mn': [0.25, 0.2]  # Row 2 sum = 0.8
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        # Check that row 1 is unchanged
        assert np.isclose(normalized_df.loc[0, 'element_Fe'], 0.25)
        # Check that row 2 is normalized
        assert np.isclose(normalized_df.loc[1, 'element_Fe'], 0.25)
        
        # Check logs
        assert logs_df.loc[0, 'status'] == 'already_normalized'
        assert logs_df.loc[1, 'status'] == 'normalized'

    def test_with_invalid_rows(self):
        """Test DataFrame with invalid rows."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'element_Fe': [0.25, 0.0, 0.2],
            'element_Cr': [0.25, 0.0, 0.2],
            'element_Ni': [0.25, 0.0, 0.2],
            'element_Mn': [0.25, 0.0, 0.2]
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        # Row 1 (index 1) should be marked invalid
        assert logs_df.loc[1, 'status'] == 'invalid'
        assert logs_df.loc[1, 'reason'] == 'zero_sum'

    def test_no_composition_columns(self):
        """Test DataFrame with no composition columns."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'bulk_modulus': [100.0, 150.0]
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        # Should return original DataFrame
        assert normalized_df.equals(df)
        assert logs_df.empty

    def test_custom_composition_columns(self):
        """Test with explicitly provided composition columns."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'comp_Fe': [0.2, 0.25],
            'comp_Cr': [0.2, 0.25],
            'other': [0.6, 0.5]
        })
        
        composition_cols = ['comp_Fe', 'comp_Cr']
        normalized_df, logs_df = normalize_dataframe(df, composition_cols=composition_cols)
        
        # Only comp_Fe and comp_Cr should be normalized
        assert np.isclose(normalized_df.loc[0, 'comp_Fe'], 0.5)
        assert np.isclose(normalized_df.loc[0, 'comp_Cr'], 0.5)
        assert normalized_df.loc[0, 'other'] == 0.6  # Unchanged


class TestNormalizationEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_values(self):
        """Test with very small composition values."""
        df = pd.DataFrame({
            'sample_id': [1],
            'element_Fe': [1e-10],
            'element_Cr': [1e-10],
            'element_Ni': [1e-10],
            'element_Mn': [1.0 - 3e-10]
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        sums = normalized_df[['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']].sum(axis=1)
        assert np.allclose(sums, 1.0, atol=NORMALIZATION_TOLERANCE)

    def test_single_element(self):
        """Test with only one composition element."""
        df = pd.DataFrame({
            'sample_id': [1],
            'element_Fe': [1.0]
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        assert np.isclose(normalized_df.loc[0, 'element_Fe'], 1.0)

    def test_precision_tolerance(self):
        """Test that values within tolerance are considered normalized."""
        df = pd.DataFrame({
            'sample_id': [1],
            'element_Fe': [0.25 + 1e-10],
            'element_Cr': [0.25 - 1e-10],
            'element_Ni': [0.25],
            'element_Mn': [0.25]
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        # Should be considered already normalized due to tolerance
        assert logs_df.loc[0, 'status'] == 'already_normalized'

    def test_large_dataframe(self):
        """Test with a larger DataFrame for performance."""
        n_rows = 1000
        df = pd.DataFrame({
            'sample_id': range(n_rows),
            'element_Fe': np.random.rand(n_rows) * 0.5,
            'element_Cr': np.random.rand(n_rows) * 0.5,
            'element_Ni': np.random.rand(n_rows) * 0.5,
            'element_Mn': np.random.rand(n_rows) * 0.5
        })
        
        normalized_df, logs_df = normalize_dataframe(df)
        
        composition_cols = ['element_Fe', 'element_Cr', 'element_Ni', 'element_Mn']
        sums = normalized_df[composition_cols].sum(axis=1)
        
        assert np.allclose(sums, 1.0, atol=NORMALIZATION_TOLERANCE)
        assert len(logs_df) == n_rows