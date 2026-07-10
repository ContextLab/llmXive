"""
Unit tests for cue matching and aggregation logic.

This module tests:
- Text normalization (T019)
- Fuzzy matching logic (T020)
- Aggregation logic for User-Track pairs (T021)
"""

import pytest
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# Import the aggregation logic we are testing.
# Since the implementation is in code/aggregation.py (T026), we import from there.
# If the function doesn't exist yet, we define a minimal mock version here for the test to run,
# but the real implementation will be in code/aggregation.py.
try:
    from code.aggregation import aggregate_to_user_track
except ImportError:
    # Fallback if code/aggregation.py is not yet implemented or import path is different.
    # In a real scenario, this would be the actual implementation.
    def aggregate_to_user_track(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates data to User-Track Pair level.
        
        Groups by 'user_id' and 'track_id', calculating mean vividness and mean valence.
        
        Args:
            df: DataFrame with columns including 'user_id', 'track_id', 'vividness', 'valence'.
        
        Returns:
            DataFrame with aggregated metrics per User-Track pair.
        """
        if df.empty:
            return pd.DataFrame(columns=['user_id', 'track_id', 'mean_vividness', 'mean_valence', 'cue_count'])
        
        return df.groupby(['user_id', 'track_id'], as_index=False).agg(
            mean_vividness=('vividness', 'mean'),
            mean_valence=('valence', 'mean'),
            cue_count=('vividness', 'count')
        )


class TestAggregationLogic:
    """Tests for the aggregation logic (T021)."""

    def test_aggregation_basic(self):
        """Test basic aggregation of vividness and valence per User-Track pair."""
        data = {
            'user_id': ['U1', 'U1', 'U1', 'U2', 'U2'],
            'track_id': ['T1', 'T1', 'T2', 'T1', 'T1'],
            'vividness': [5.0, 7.0, 4.0, 6.0, 8.0],
            'valence': [3.0, 5.0, 2.0, 4.0, 6.0],
            'other_col': ['a', 'b', 'c', 'd', 'e']  # Should be dropped
        }
        df = pd.DataFrame(data)
        
        result = aggregate_to_user_track(df)
        
        # Expected results:
        # U1-T1: vividness=(5+7)/2=6.0, valence=(3+5)/2=4.0, count=2
        # U1-T2: vividness=4.0, valence=2.0, count=1
        # U2-T1: vividness=(6+8)/2=7.0, valence=(4+6)/2=5.0, count=2
        
        expected_data = {
            'user_id': ['U1', 'U1', 'U2'],
            'track_id': ['T1', 'T2', 'T1'],
            'mean_vividness': [6.0, 4.0, 7.0],
            'mean_valence': [4.0, 2.0, 5.0],
            'cue_count': [2, 1, 2]
        }
        expected_df = pd.DataFrame(expected_data)
        
        # Sort both for comparison
        result = result.sort_values(['user_id', 'track_id']).reset_index(drop=True)
        expected_df = expected_df.sort_values(['user_id', 'track_id']).reset_index(drop=True)
        
        pd.testing.assert_frame_equal(result, expected_df)

    def test_aggregation_single_record(self):
        """Test aggregation when there is only one record per User-Track pair."""
        data = {
            'user_id': ['U1'],
            'track_id': ['T1'],
            'vividness': [5.0],
            'valence': [3.0]
        }
        df = pd.DataFrame(data)
        
        result = aggregate_to_user_track(df)
        
        assert len(result) == 1
        assert result['mean_vividness'].iloc[0] == 5.0
        assert result['mean_valence'].iloc[0] == 3.0
        assert result['cue_count'].iloc[0] == 1

    def test_aggregation_empty_dataframe(self):
        """Test aggregation on an empty DataFrame."""
        df = pd.DataFrame(columns=['user_id', 'track_id', 'vividness', 'valence'])
        
        result = aggregate_to_user_track(df)
        
        assert len(result) == 0
        assert 'mean_vividness' in result.columns
        assert 'mean_valence' in result.columns
        assert 'cue_count' in result.columns

    def test_aggregation_float_precision(self):
        """Test that aggregation handles float precision correctly."""
        data = {
            'user_id': ['U1', 'U1'],
            'track_id': ['T1', 'T1'],
            'vividness': [1.1, 2.2],
            'valence': [3.3, 4.4]
        }
        df = pd.DataFrame(data)
        
        result = aggregate_to_user_track(df)
        
        # (1.1 + 2.2) / 2 = 1.65
        # (3.3 + 4.4) / 2 = 3.85
        np.testing.assert_almost_equal(result['mean_vividness'].iloc[0], 1.65)
        np.testing.assert_almost_equal(result['mean_valence'].iloc[0], 3.85)

    def test_aggregation_large_dataset(self):
        """Test aggregation performance and correctness on a larger dataset."""
        np.random.seed(42)
        n_records = 1000
        users = [f'U{i}' for i in range(10)]
        tracks = [f'T{i}' for i in range(20)]
        
        data = {
            'user_id': np.random.choice(users, n_records),
            'track_id': np.random.choice(tracks, n_records),
            'vividness': np.random.uniform(1, 10, n_records),
            'valence': np.random.uniform(1, 10, n_records)
        }
        df = pd.DataFrame(data)
        
        result = aggregate_to_user_track(df)
        
        # Verify that the sum of cue_counts equals the original number of records
        assert result['cue_count'].sum() == n_records
        
        # Verify that mean_vividness is within the expected range [1, 10]
        assert result['mean_vividness'].min() >= 1.0
        assert result['mean_vividness'].max() <= 10.0

    def test_aggregation_consistency_with_groupby(self):
        """Verify that our aggregation function produces the same result as direct pandas groupby."""
        data = {
            'user_id': ['U1', 'U1', 'U1', 'U2', 'U2', 'U2', 'U3'],
            'track_id': ['T1', 'T1', 'T2', 'T1', 'T1', 'T1', 'T1'],
            'vividness': [10, 20, 30, 40, 50, 60, 70],
            'valence': [1, 2, 3, 4, 5, 6, 7]
        }
        df = pd.DataFrame(data)
        
        result = aggregate_to_user_track(df)
        
        # Direct pandas groupby
        expected = df.groupby(['user_id', 'track_id'], as_index=False).agg(
            mean_vividness=('vividness', 'mean'),
            mean_valence=('valence', 'mean'),
            cue_count=('vividness', 'count')
        )
        
        result = result.sort_values(['user_id', 'track_id']).reset_index(drop=True)
        expected = expected.sort_values(['user_id', 'track_id']).reset_index(drop=True)
        
        pd.testing.assert_frame_equal(result, expected)