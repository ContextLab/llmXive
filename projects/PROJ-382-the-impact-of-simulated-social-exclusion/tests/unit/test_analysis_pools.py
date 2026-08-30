"""
Unit tests for pool splitting logic (RCT vs Non-RCT) in code/preprocess.py.

This module verifies that the `split_pools` function correctly separates
datasets into 'causal_pool' (randomized=true) and 'associational_pool'
(randomized=false or unknown) based on the specification for User Story 2.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
_project_root = Path(__file__).resolve().parent.parent.parent
_code_path = _project_root / "code"
if str(_code_path) not in sys.path:
    sys.path.insert(0, str(_code_path))

from preprocess import split_pools
from config import get_project_paths

class TestSplitPools:
    """Tests for the split_pools function."""

    def test_split_pools_basic_rct_vs_non_rct(self):
        """Test basic splitting of RCT and Non-RCT data."""
        # Create a synthetic dataset that mimics real data structure
        # We use synthetic data ONLY for testing the logic, not for the final analysis.
        # The actual data comes from real OSF downloads.
        data = {
            'study_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'condition': [0, 1, 0, 1, 0],
            'prosocial_amount': [5.0, 3.0, 6.0, 2.0, 4.0],
            'randomized': [True, False, True, False, True],
            'source': ['OSF1', 'OSF2', 'OSF3', 'OSF4', 'OSF5']
        }
        df = pd.DataFrame(data)

        causal_pool, associational_pool = split_pools(df)

        # Verify causal pool contains only randomized=True
        assert len(causal_pool) == 3
        assert all(causal_pool['randomized'] == True)
        assert set(causal_pool['study_id']) == {'S1', 'S3', 'S5'}

        # Verify associational pool contains only randomized=False
        assert len(associational_pool) == 2
        assert all(associational_pool['randomized'] == False)
        assert set(associational_pool['study_id']) == {'S2', 'S4'}

    def test_split_pools_handles_missing_randomized_column(self):
        """Test that the function handles missing 'randomized' column gracefully."""
        data = {
            'study_id': ['S1', 'S2'],
            'condition': [0, 1],
            'prosocial_amount': [5.0, 3.0]
        }
        df = pd.DataFrame(data)

        # The function should treat missing 'randomized' as False (associational)
        # or raise an error depending on implementation. We expect it to handle it.
        # Based on typical data pipeline behavior, we assume it defaults to False.
        causal_pool, associational_pool = split_pools(df)

        # All rows should go to associational pool if randomized is missing or False
        assert len(causal_pool) == 0
        assert len(associational_pool) == 2
        assert all(associational_pool['randomized'] == False)

    def test_split_pools_preserves_data_integrity(self):
        """Test that no data is lost or modified during the split."""
        data = {
            'study_id': ['S1', 'S2', 'S3', 'S4'],
            'condition': [0, 1, 0, 1],
            'prosocial_amount': [5.0, 3.0, 6.0, 2.0],
            'randomized': [True, False, True, False],
            'extra_col': ['A', 'B', 'C', 'D']
        }
        df = pd.DataFrame(data)

        causal_pool, associational_pool = split_pools(df)

        # Check that all original rows are accounted for
        combined = pd.concat([causal_pool, associational_pool])
        assert len(combined) == len(df)
        
        # Check that original values are preserved
        assert set(combined['study_id']) == set(df['study_id'])
        assert set(combined['extra_col']) == set(df['extra_col'])
        
        # Check that prosocial_amount is preserved
        assert np.allclose(sorted(combined['prosocial_amount']), sorted(df['prosocial_amount']))

    def test_split_pools_empty_dataframe(self):
        """Test splitting an empty dataframe."""
        df = pd.DataFrame(columns=['study_id', 'condition', 'prosocial_amount', 'randomized'])
        
        causal_pool, associational_pool = split_pools(df)
        
        assert len(causal_pool) == 0
        assert len(associational_pool) == 0

    def test_split_pools_all_causal(self):
        """Test splitting when all data is from RCTs."""
        data = {
            'study_id': ['S1', 'S2'],
            'condition': [0, 1],
            'prosocial_amount': [5.0, 3.0],
            'randomized': [True, True]
        }
        df = pd.DataFrame(data)

        causal_pool, associational_pool = split_pools(df)

        assert len(causal_pool) == 2
        assert len(associational_pool) == 0

    def test_split_pools_all_associational(self):
        """Test splitting when all data is from non-RCTs."""
        data = {
            'study_id': ['S1', 'S2'],
            'condition': [0, 1],
            'prosocial_amount': [5.0, 3.0],
            'randomized': [False, False]
        }
        df = pd.DataFrame(data)

        causal_pool, associational_pool = split_pools(df)

        assert len(causal_pool) == 0
        assert len(associational_pool) == 2

    def test_split_pools_with_none_randomized_values(self):
        """Test handling of None/NaN in randomized column."""
        data = {
            'study_id': ['S1', 'S2', 'S3'],
            'condition': [0, 1, 0],
            'prosocial_amount': [5.0, 3.0, 6.0],
            'randomized': [True, None, False]
        }
        df = pd.DataFrame(data)

        causal_pool, associational_pool = split_pools(df)

        # True goes to causal, None and False go to associational
        assert len(causal_pool) == 1
        assert causal_pool.iloc[0]['study_id'] == 'S1'
        
        assert len(associational_pool) == 2
        assert set(associational_pool['study_id']) == {'S2', 'S3'}

    def test_split_pools_returns_correct_types(self):
        """Test that the function returns pandas DataFrames."""
        data = {
            'study_id': ['S1'],
            'condition': [0],
            'prosocial_amount': [5.0],
            'randomized': [True]
        }
        df = pd.DataFrame(data)

        causal_pool, associational_pool = split_pools(df)

        assert isinstance(causal_pool, pd.DataFrame)
        assert isinstance(associational_pool, pd.DataFrame)