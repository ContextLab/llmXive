"""
Unit tests for alloy system grouping derivation logic.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.model.derive_groups import (
    get_composition_columns,
    derive_alloy_system_key,
    add_alloy_system_grouping,
    get_unique_alloy_systems,
    count_samples_per_group
)


class TestGetCompositionColumns:
    """Tests for composition column detection."""

    def test_detects_elem_prefix(self):
        """Should detect columns starting with 'elem_'."""
        df = pd.DataFrame({
            'elem_Fe': [0.5],
            'elem_Cr': [0.3],
            'other_col': [1.0]
        })
        cols = get_composition_columns(df)
        assert 'elem_Fe' in cols
        assert 'elem_Cr' in cols
        assert 'other_col' not in cols

    def test_detects_composition_prefix(self):
        """Should detect columns starting with 'composition_'."""
        df = pd.DataFrame({
            'composition_Ni': [0.4],
            'composition_Mn': [0.2],
            'target': [100.0]
        })
        cols = get_composition_columns(df)
        assert 'composition_Ni' in cols
        assert 'composition_Mn' in cols
        assert 'target' not in cols

    def test_sorted_output(self):
        """Should return columns in sorted order."""
        df = pd.DataFrame({
            'elem_Zr': [0.1],
            'elem_Al': [0.1],
            'elem_Co': [0.1]
        })
        cols = get_composition_columns(df)
        assert cols == ['elem_Al', 'elem_Co', 'elem_Zr']

    def test_empty_dataframe(self):
        """Should return empty list for empty dataframe."""
        df = pd.DataFrame()
        cols = get_composition_columns(df)
        assert cols == []


class TestDeriveAlloySystemKey:
    """Tests for deriving alloy system keys from rows."""

    def test_simple_binary_alloy(self):
        """Should derive correct key for a binary alloy."""
        row = pd.Series({
            'elem_Fe': 0.5,
            'elem_Cr': 0.5,
            'elem_Ni': 0.0
        })
        cols = ['elem_Fe', 'elem_Cr', 'elem_Ni']
        key = derive_alloy_system_key(row, cols)
        assert key == ('Cr', 'Fe')

    def test_ignores_zero_compositions(self):
        """Should ignore elements with zero or near-zero composition."""
        row = pd.Series({
            'elem_Fe': 0.99,
            'elem_Cr': 0.00,
            'elem_Ni': 1e-10
        })
        cols = ['elem_Fe', 'elem_Cr', 'elem_Ni']
        key = derive_alloy_system_key(row, cols)
        assert key == ('Fe',)

    def test_handles_missing_elements(self):
        """Should handle rows where some elements are missing."""
        row = pd.Series({
            'elem_Fe': 0.5,
            'elem_Ni': 0.5
        })
        cols = ['elem_Fe', 'elem_Cr', 'elem_Ni']
        key = derive_alloy_system_key(row, cols)
        assert key == ('Fe', 'Ni')

    def test_sorted_key_independence(self):
        """Should produce same key regardless of column order."""
        row1 = pd.Series({'elem_Fe': 0.5, 'elem_Cr': 0.5})
        row2 = pd.Series({'elem_Cr': 0.5, 'elem_Fe': 0.5})

        key1 = derive_alloy_system_key(row1, ['elem_Fe', 'elem_Cr'])
        key2 = derive_alloy_system_key(row2, ['elem_Cr', 'elem_Fe'])

        assert key1 == key2

    def test_composition_prefix_support(self):
        """Should work with 'composition_' prefix."""
        row = pd.Series({
            'composition_Co': 0.2,
            'composition_Cr': 0.2,
            'composition_Fe': 0.2,
            'composition_Mn': 0.2,
            'composition_Ni': 0.2
        })
        cols = list(row.index)
        key = derive_alloy_system_key(row, cols)
        assert key == ('Co', 'Cr', 'Fe', 'Mn', 'Ni')


class TestAddAlloySystemGrouping:
    """Tests for adding grouping column to DataFrame."""

    def test_adds_column(self):
        """Should add 'alloy_system' column."""
        df = pd.DataFrame({
            'elem_Fe': [0.5, 0.3],
            'elem_Cr': [0.5, 0.7],
            'elem_Ni': [0.0, 0.0]
        })
        result = add_alloy_system_grouping(df)
        assert 'alloy_system' in result.columns

    def test_correct_grouping(self):
        """Should correctly group samples by element set."""
        df = pd.DataFrame({
            'elem_Fe': [0.5, 0.5, 0.0],
            'elem_Cr': [0.5, 0.0, 0.5],
            'elem_Ni': [0.0, 0.5, 0.5]
        })
        result = add_alloy_system_grouping(df)

        # First two rows should be same group (Fe, Cr) and (Fe, Ni) respectively
        # Actually, row 0: (Cr, Fe), row 1: (Fe, Ni), row 2: (Cr, Ni)
        assert result.iloc[0]['alloy_system'] == ('Cr', 'Fe')
        assert result.iloc[1]['alloy_system'] == ('Fe', 'Ni')
        assert result.iloc[2]['alloy_system'] == ('Cr', 'Ni')

    def test_same_elements_different_order(self):
        """Should group samples with same elements together."""
        df = pd.DataFrame({
            'elem_Fe': [0.5, 0.3],
            'elem_Cr': [0.5, 0.7],
            'elem_Ni': [0.0, 0.0]
        })
        result = add_alloy_system_grouping(df)

        # Both rows have Fe and Cr, so same group
        assert result.iloc[0]['alloy_system'] == result.iloc[1]['alloy_system']

    def test_no_composition_columns(self):
        """Should handle dataframe with no composition columns."""
        df = pd.DataFrame({
            'target': [100.0, 150.0],
            'other': [1.0, 2.0]
        })
        result = add_alloy_system_grouping(df)
        assert result['alloy_system'].tolist() == ['unknown', 'unknown']


class TestGetUniqueAlloySystems:
    """Tests for retrieving unique alloy systems."""

    def test_returns_unique_systems(self):
        """Should return list of unique alloy systems."""
        df = pd.DataFrame({
            'alloy_system': [('Fe', 'Cr'), ('Fe', 'Ni'), ('Fe', 'Cr'), ('Co', 'Fe')]
        })
        systems = get_unique_alloy_systems(df)
        assert len(systems) == 3
        assert ('Fe', 'Cr') in systems
        assert ('Fe', 'Ni') in systems
        assert ('Co', 'Fe') in systems

    def test_raises_if_column_missing(self):
        """Should raise error if alloy_system column is missing."""
        df = pd.DataFrame({'other': [1, 2, 3]})
        with pytest.raises(ValueError):
            get_unique_alloy_systems(df)


class TestCountSamplesPerGroup:
    """Tests for counting samples per group."""

    def test_counts_correctly(self):
        """Should count samples per group correctly."""
        df = pd.DataFrame({
            'alloy_system': [('Fe', 'Cr'), ('Fe', 'Cr'), ('Fe', 'Ni')]
        })
        counts = count_samples_per_group(df)

        assert len(counts) == 2
        fe_cr_row = counts[counts['alloy_system'] == ('Fe', 'Cr')]
        fe_ni_row = counts[counts['alloy_system'] == ('Fe', 'Ni')]

        assert fe_cr_row['count'].values[0] == 2
        assert fe_ni_row['count'].values[0] == 1

    def test_raises_if_column_missing(self):
        """Should raise error if alloy_system column is missing."""
        df = pd.DataFrame({'other': [1, 2, 3]})
        with pytest.raises(ValueError):
            count_samples_per_group(df)