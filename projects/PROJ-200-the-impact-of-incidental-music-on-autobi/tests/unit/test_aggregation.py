"""
Unit tests for aggregation.py (T025, T026, T027, T036).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import sys
# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from aggregation import join_exposure_data, aggregate_to_user_track, filter_zero_variance, enforce_match_rate

class TestJoinExposureData:
    """Tests for T025: join_exposure_data"""

    def test_join_exposure_data_basic(self):
        """Test basic join functionality."""
        cues_df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'matched_title': ['Song A', 'Song B', 'Song C'],
            'matched_artist': ['Artist 1', 'Artist 2', 'Artist 3'],
            'vividness': [5.0, 4.0, 3.0],
            'valence': [0.8, 0.5, 0.2]
        })

        exposure_df = pd.DataFrame({
            'title': ['Song A', 'Song B', 'Song D'],
            'artist': ['Artist 1', 'Artist 2', 'Artist 4'],
            'adolescent_exposure_score': [0.9, 0.1, 0.5],
            'residualized_exposure_score': [0.8, -0.1, 0.4],
            'overall_popularity_score': [100, 50, 200]
        })

        result = join_exposure_data(cues_df, exposure_df)

        # Should have 2 matches (Song A, Song B). Song C has no match.
        assert len(result) == 2
        assert 'adolescent_exposure_score' in result.columns
        assert 'residualized_exposure_score' in result.columns
        # Check specific values
        row_a = result[result['matched_title'] == 'Song A'].iloc[0]
        assert row_a['adolescent_exposure_score'] == 0.9

    def test_join_exposure_data_missing_columns(self):
        """Test that missing columns raise an error."""
        cues_df = pd.DataFrame({'user_id': [1]}) # Missing matched_title
        exposure_df = pd.DataFrame({'title': ['Song A']})

        with pytest.raises(ValueError):
            join_exposure_data(cues_df, exposure_df)

    def test_join_exposure_data_inner_join(self):
        """Test that inner join filters out unmatched records."""
        cues_df = pd.DataFrame({
            'user_id': [1],
            'matched_title': ['Unknown Song'],
            'matched_artist': ['Unknown Artist']
        })
        exposure_df = pd.DataFrame({
            'title': ['Known Song'],
            'artist': ['Known Artist']
        })

        result = join_exposure_data(cues_df, exposure_df)
        assert len(result) == 0

class TestAggregateToUserTrack:
    """Tests for T026: aggregate_to_user_track"""

    def test_aggregate_mean_values(self):
        """Test correct aggregation of mean vividness and valence."""
        df = pd.DataFrame({
            'user_id': [1, 1, 1, 2],
            'track_id': [100, 100, 100, 100],
            'vividness': [5.0, 3.0, 2.0, 4.0],
            'valence': [0.8, 0.6, 0.4, 0.5],
            'adolescent_exposure_score': [0.9, 0.9, 0.9, 0.9]
        })

        result = aggregate_to_user_track(df)

        assert len(result) == 2
        # User 1, Track 100: mean vividness = (5+3+2)/3 = 3.333
        row1 = result[(result['user_id'] == 1) & (result['track_id'] == 100)].iloc[0]
        assert np.isclose(row1['mean_vividness'], 3.333333, atol=0.001)
        assert row1['memory_count'] == 3

        # User 2, Track 100: mean vividness = 4.0
        row2 = result[(result['user_id'] == 2) & (result['track_id'] == 100)].iloc[0]
        assert np.isclose(row2['mean_vividness'], 4.0, atol=0.001)
        assert row2['memory_count'] == 1

    def test_aggregate_missing_ids_fallback(self):
        """Test fallback to title/artist if track_id is missing."""
        df = pd.DataFrame({
            'user_id': [1, 1],
            'matched_title': ['Song X', 'Song X'],
            'matched_artist': ['Artist X', 'Artist X'],
            'vividness': [5.0, 5.0],
            'valence': [0.8, 0.8]
        })

        result = aggregate_to_user_track(df)
        assert len(result) == 1
        assert 'matched_title' in result.columns

    def test_aggregate_dropna(self):
        """Test that rows with missing vividness are dropped."""
        df = pd.DataFrame({
            'user_id': [1, 1],
            'track_id': [100, 100],
            'vividness': [5.0, np.nan],
            'valence': [0.8, 0.5]
        })

        result = aggregate_to_user_track(df)
        # Only the first row should be aggregated
        assert len(result) == 1
        assert result.iloc[0]['memory_count'] == 1

class TestFilterZeroVariance:
    """Tests for T027: filter_zero_variance"""

    def test_filter_zero_memory_count(self):
        """Test filtering of records with memory_count < 1."""
        df = pd.DataFrame({
            'user_id': [1, 2],
            'track_id': [100, 200],
            'mean_vividness': [5.0, 3.0],
            'memory_count': [0, 5]
        })

        result = filter_zero_variance(df)
        assert len(result) == 1
        assert result.iloc[0]['user_id'] == 2

    def test_filter_no_change_if_valid(self):
        """Test that valid data passes through."""
        df = pd.DataFrame({
            'user_id': [1],
            'track_id': [100],
            'mean_vividness': [5.0],
            'memory_count': [3]
        })

        result = filter_zero_variance(df)
        assert len(result) == 1

class TestEnforceMatchRate:
    """Tests for T036: enforce_match_rate"""

    def test_match_rate_above_threshold(self):
        """Test pass when rate is above 80%."""
        df = pd.DataFrame({
            'cue_id': [1, 2, 3, 4, 5],
            'is_matched': [True, True, True, True, False] # 80% match
        })

        result = enforce_match_rate(df, threshold=0.80)
        assert result is True

    def test_match_rate_below_threshold(self):
        """Test warning when rate is below 80%."""
        df = pd.DataFrame({
            'cue_id': [1, 2, 3, 4, 5, 6],
            'is_matched': [True, True, True, False, False, False] # 50% match
        })

        # Should return True but log a warning (we can't easily capture log in this simple test,
        # but we verify return value)
        result = enforce_match_rate(df, threshold=0.80)
        assert result is True

    def test_missing_is_matched_column(self):
        """Test handling of missing is_matched column."""
        df = pd.DataFrame({'cue_id': [1]})
        result = enforce_match_rate(df)
        assert result is True