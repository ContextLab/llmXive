import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_project_root


class TestMergeLogicInChIKey:
    """Unit tests for merge logic on InChIKey (handling missing data/NaNs)."""

    @pytest.fixture
    def sample_descriptors_df(self):
        """Create a sample descriptors DataFrame with InChIKey."""
        data = {
            'InChIKey': ['KEY1', 'KEY2', 'KEY3', 'KEY4'],
            'MW': [150.0, 200.0, 300.0, 400.0],
            'LogP': [1.2, 2.5, 3.1, 4.0],
            'num_h_acceptors': [2, 3, 5, 6]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_resistance_df(self):
        """Create a sample resistance DataFrame with InChIKey."""
        data = {
            'InChIKey': ['KEY2', 'KEY3', 'KEY5', 'KEY6'],
            'resistance_frequency': [0.1, 0.8, 0.05, 0.9],
            'organism': ['E. coli', 'S. aureus', 'K. pneumoniae', 'E. coli']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_resistance_with_nan(self):
        """Create a sample resistance DataFrame with NaN values."""
        data = {
            'InChIKey': ['KEY2', None, 'KEY5', 'KEY6'],
            'resistance_frequency': [0.1, 0.8, 0.05, 0.9],
            'organism': ['E. coli', 'S. aureus', 'K. pneumoniae', 'E. coli']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_descriptors_with_nan(self):
        """Create a sample descriptors DataFrame with NaN InChIKey."""
        data = {
            'InChIKey': ['KEY1', None, 'KEY3', 'KEY4'],
            'MW': [150.0, 200.0, 300.0, 400.0],
            'LogP': [1.2, 2.5, 3.1, 4.0],
            'num_h_acceptors': [2, 3, 5, 6]
        }
        return pd.DataFrame(data)

    def test_inner_merge_excludes_missing_matches(self, sample_descriptors_df, sample_resistance_df):
        """Test that inner merge only keeps compounds present in both datasets."""
        # Expected: KEY2 and KEY3 are in both
        expected_keys = {'KEY2', 'KEY3'}
        
        # Perform inner merge
        merged = pd.merge(
            sample_descriptors_df,
            sample_resistance_df,
            on='InChIKey',
            how='inner'
        )
        
        assert set(merged['InChIKey'].unique()) == expected_keys
        assert len(merged) == 2

    def test_left_merge_keeps_all_descriptors(self, sample_descriptors_df, sample_resistance_df):
        """Test that left merge keeps all descriptors and fills missing resistance with NaN."""
        # Expected: All 4 descriptors, but KEY1 and KEY4 will have NaN resistance
        merged = pd.merge(
            sample_descriptors_df,
            sample_resistance_df,
            on='InChIKey',
            how='left'
        )
        
        assert len(merged) == 4
        assert set(merged['InChIKey'].unique()) == {'KEY1', 'KEY2', 'KEY3', 'KEY4'}
        
        # Check that KEY1 and KEY4 have NaN for resistance columns
        key1_row = merged[merged['InChIKey'] == 'KEY1']
        key4_row = merged[merged['InChIKey'] == 'KEY4']
        
        assert pd.isna(key1_row['resistance_frequency'].iloc[0])
        assert pd.isna(key1_row['organism'].iloc[0])
        assert pd.isna(key4_row['resistance_frequency'].iloc[0])
        assert pd.isna(key4_row['organism'].iloc[0])
        
        # Check that KEY2 and KEY3 have valid resistance data
        key2_row = merged[merged['InChIKey'] == 'KEY2']
        key3_row = merged[merged['InChIKey'] == 'KEY3']
        
        assert not pd.isna(key2_row['resistance_frequency'].iloc[0])
        assert not pd.isna(key3_row['resistance_frequency'].iloc[0])

    def test_right_merge_keeps_all_resistance(self, sample_descriptors_df, sample_resistance_df):
        """Test that right merge keeps all resistance data and fills missing descriptors with NaN."""
        # Expected: All 4 resistance entries, but KEY5 and KEY6 will have NaN descriptors
        merged = pd.merge(
            sample_descriptors_df,
            sample_resistance_df,
            on='InChIKey',
            how='right'
        )
        
        assert len(merged) == 4
        assert set(merged['InChIKey'].unique()) == {'KEY2', 'KEY3', 'KEY5', 'KEY6'}
        
        # Check that KEY5 and KEY6 have NaN for descriptor columns
        key5_row = merged[merged['InChIKey'] == 'KEY5']
        key6_row = merged[merged['InChIKey'] == 'KEY6']
        
        assert pd.isna(key5_row['MW'].iloc[0])
        assert pd.isna(key5_row['LogP'].iloc[0])
        assert pd.isna(key6_row['MW'].iloc[0])
        assert pd.isna(key6_row['LogP'].iloc[0])

    def test_outer_merge_keeps_all(self, sample_descriptors_df, sample_resistance_df):
        """Test that outer merge keeps all records from both datasets."""
        # Expected: All unique keys from both datasets
        expected_keys = {'KEY1', 'KEY2', 'KEY3', 'KEY4', 'KEY5', 'KEY6'}
        
        merged = pd.merge(
            sample_descriptors_df,
            sample_resistance_df,
            on='InChIKey',
            how='outer'
        )
        
        assert set(merged['InChIKey'].unique()) == expected_keys
        assert len(merged) == 6

    def test_merge_handles_nan_inchikey_in_descriptors(self, sample_descriptors_with_nan, sample_resistance_df):
        """Test that NaN InChIKey in descriptors are excluded from inner/left merge."""
        # Inner merge should exclude NaN keys
        merged_inner = pd.merge(
            sample_descriptors_with_nan,
            sample_resistance_df,
            on='InChIKey',
            how='inner'
        )
        
        # NaN keys should not match anything
        assert len(merged_inner) == 2  # Only KEY2 and KEY3
        assert not merged_inner['InChIKey'].isna().any()
        
        # Left merge should include NaN keys but with NaN resistance
        merged_left = pd.merge(
            sample_descriptors_with_nan,
            sample_resistance_df,
            on='InChIKey',
            how='left'
        )
        
        assert len(merged_left) == 4
        # One row should have NaN InChIKey
        nan_rows = merged_left[merged_left['InChIKey'].isna()]
        assert len(nan_rows) == 1
        assert pd.isna(nan_rows['resistance_frequency'].iloc[0])

    def test_merge_handles_nan_inchikey_in_resistance(self, sample_descriptors_df, sample_resistance_with_nan):
        """Test that NaN InChIKey in resistance are excluded from inner/right merge."""
        # Inner merge should exclude NaN keys
        merged_inner = pd.merge(
            sample_descriptors_df,
            sample_resistance_with_nan,
            on='InChIKey',
            how='inner'
        )
        
        assert len(merged_inner) == 2  # Only KEY2 and KEY3
        assert not merged_inner['InChIKey'].isna().any()
        
        # Right merge should include NaN keys but with NaN descriptors
        merged_right = pd.merge(
            sample_descriptors_df,
            sample_resistance_with_nan,
            on='InChIKey',
            how='right'
        )
        
        assert len(merged_right) == 4
        # One row should have NaN InChIKey
        nan_rows = merged_right[merged_right['InChIKey'].isna()]
        assert len(nan_rows) == 1
        assert pd.isna(nan_rows['MW'].iloc[0])

    def test_merge_preserves_data_types(self, sample_descriptors_df, sample_resistance_df):
        """Test that merge preserves numeric data types for non-matching columns."""
        merged = pd.merge(
            sample_descriptors_df,
            sample_resistance_df,
            on='InChIKey',
            how='left'
        )
        
        # Check that numeric columns remain numeric
        assert pd.api.types.is_float_dtype(merged['MW'])
        assert pd.api.types.is_float_dtype(merged['LogP'])
        assert pd.api.types.is_float_dtype(merged['resistance_frequency'])
        
        # Check that string columns remain object/string
        assert pd.api.types.is_object_dtype(merged['organism'])

    def test_merge_with_duplicate_inchikey_handles_correctly(self):
        """Test merge behavior when duplicate InChIKeys exist in one or both datasets."""
        # Create duplicates in descriptors
        desc_dup = pd.DataFrame({
            'InChIKey': ['KEY1', 'KEY1', 'KEY2'],
            'MW': [150.0, 151.0, 200.0],
            'LogP': [1.2, 1.3, 2.5]
        })
        
        # Create duplicates in resistance
        res_dup = pd.DataFrame({
            'InChIKey': ['KEY1', 'KEY1', 'KEY3'],
            'resistance_frequency': [0.1, 0.2, 0.8],
            'organism': ['E. coli', 'E. coli', 'S. aureus']
        })
        
        # Merge should produce cartesian product for duplicates
        merged = pd.merge(desc_dup, res_dup, on='InChIKey', how='inner')
        
        # KEY1 appears twice in each, so should have 2*2=4 rows for KEY1
        # Plus 1 row for KEY2 (no match) and 1 row for KEY3 (no match) - wait, KEY2 and KEY3 don't match
        # Actually: KEY1 (2x2 = 4 rows), KEY2 (no match in res), KEY3 (no match in desc)
        # So only KEY1 matches
        assert len(merged[merged['InChIKey'] == 'KEY1']) == 4
        
        # Verify cartesian product values
        key1_rows = merged[merged['InChIKey'] == 'KEY1']
        assert set(key1_rows['MW'].unique()) == {150.0, 151.0}
        assert set(key1_rows['resistance_frequency'].unique()) == {0.1, 0.2}

    def test_merge_empty_dataframe(self):
        """Test merge with empty DataFrames."""
        empty_desc = pd.DataFrame(columns=['InChIKey', 'MW', 'LogP'])
        empty_res = pd.DataFrame(columns=['InChIKey', 'resistance_frequency', 'organism'])
        
        # Empty merge should return empty
        merged = pd.merge(empty_desc, empty_res, on='InChIKey', how='inner')
        assert len(merged) == 0
        
        # Left merge with empty resistance
        desc_only = pd.DataFrame({'InChIKey': ['KEY1'], 'MW': [150.0]})
        merged_left = pd.merge(desc_only, empty_res, on='InChIKey', how='left')
        assert len(merged_left) == 1
        assert pd.isna(merged_left['resistance_frequency'].iloc[0])

    def test_merge_with_suffixes_for_overlapping_columns(self):
        """Test that merge handles overlapping column names with suffixes."""
        desc = pd.DataFrame({
            'InChIKey': ['KEY1', 'KEY2'],
            'MW': [150.0, 200.0],
            'source': ['chembl', 'zinc']
        })
        
        res = pd.DataFrame({
            'InChIKey': ['KEY1', 'KEY2'],
            'MW': [155.0, 205.0],  # Overlapping column name
            'resistance_frequency': [0.1, 0.8]
        })
        
        merged = pd.merge(desc, res, on='InChIKey', how='inner', suffixes=('_desc', '_res'))
        
        assert 'MW_desc' in merged.columns
        assert 'MW_res' in merged.columns
        assert 'source' in merged.columns
        
        # Verify values are correctly assigned
        key1 = merged[merged['InChIKey'] == 'KEY1']
        assert key1['MW_desc'].iloc[0] == 150.0
        assert key1['MW_res'].iloc[0] == 155.0
        assert key1['source'].iloc[0] == 'chembl'