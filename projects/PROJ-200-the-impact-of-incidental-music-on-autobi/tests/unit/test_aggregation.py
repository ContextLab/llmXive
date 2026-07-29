"""
Unit tests for aggregation module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from aggregation import (
    join_exposure_data,
    aggregate_to_user_track,
    filter_zero_variance,
    enforce_match_rate,
    load_aggregated_data
)

class TestJoinExposureData:
    """Tests for join_exposure_data function."""
    
    def test_join_exposure_data_basic(self):
        """Test basic joining of exposure data with cues."""
        # Create mock cues DataFrame
        cues_df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'track_id': [101, 102, 103],
            'mean_vividness': [0.8, 0.6, 0.9],
            'mean_valence': [0.7, 0.5, 0.8]
        })
        
        # Create mock cohort DataFrame
        cohort_df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'track_id': [101, 102, 103],
            'adolescent_exposure_ratio': [0.5, 0.7, 0.3],
            'overall_popularity_score': [0.8, 0.6, 0.9],
            'total_listens': [10, 15, 8]
        })
        
        # Perform join
        result = join_exposure_data(cues_df, cohort_df)
        
        # Assert result
        assert len(result) == 3
        assert 'adolescent_exposure_ratio' in result.columns
        assert 'overall_popularity_score' in result.columns
        assert 'mean_vividness' in result.columns
        assert 'mean_valence' in result.columns
        
        # Check values
        assert result.iloc[0]['adolescent_exposure_ratio'] == 0.5
        assert result.iloc[1]['mean_vividness'] == 0.6
    
    def test_join_exposure_data_missing_columns(self):
        """Test that missing columns raise an error."""
        cues_df = pd.DataFrame({
            'user_id': [1],
            'track_id': [101],
            'mean_vividness': [0.8]
            # Missing mean_valence
        })
        
        cohort_df = pd.DataFrame({
            'user_id': [1],
            'track_id': [101],
            'adolescent_exposure_ratio': [0.5],
            'overall_popularity_score': [0.8]
        })
        
        with pytest.raises(ValueError):
            join_exposure_data(cues_df, cohort_df)
    
    def test_join_exposure_data_no_match(self):
        """Test joining when there are no matching keys."""
        cues_df = pd.DataFrame({
            'user_id': [1],
            'track_id': [101],
            'mean_vividness': [0.8],
            'mean_valence': [0.7]
        })
        
        cohort_df = pd.DataFrame({
            'user_id': [2],
            'track_id': [102],
            'adolescent_exposure_ratio': [0.5],
            'overall_popularity_score': [0.8]
        })
        
        result = join_exposure_data(cues_df, cohort_df)
        
        assert len(result) == 0

class TestAggregateToUserTrack:
    """Tests for aggregate_to_user_track function."""
    
    def test_aggregate_to_user_track_basic(self):
        """Test basic aggregation to User-Track pairs."""
        # Create mock cues DataFrame
        cues_df = pd.DataFrame({
            'user_id': [1, 1, 2, 2, 2],
            'track_id': [101, 101, 102, 102, 102],
            'cue_id': [1, 2, 3, 4, 5]
        })
        
        # Create mock cues metadata
        cues_metadata = pd.DataFrame({
            'cue_id': [1, 2, 3, 4, 5],
            'vividness': [0.8, 0.9, 0.6, 0.7, 0.8],
            'valence': [0.7, 0.6, 0.5, 0.6, 0.7]
        })
        
        # Perform aggregation
        result = aggregate_to_user_track(cues_df, cues_metadata)
        
        # Assert result
        assert len(result) == 2  # 2 unique user-track pairs
        
        # Check user 1, track 101
        user1_track101 = result[(result['user_id'] == 1) & (result['track_id'] == 101)]
        assert len(user1_track101) == 1
        assert abs(user1_track101.iloc[0]['mean_vividness'] - 0.85) < 0.01
        assert user1_track101.iloc[0]['cue_count'] == 2
        
        # Check user 2, track 102
        user2_track102 = result[(result['user_id'] == 2) & (result['track_id'] == 102)]
        assert len(user2_track102) == 1
        assert abs(user2_track102.iloc[0]['mean_vividness'] - 0.7) < 0.01
        assert user2_track102.iloc[0]['cue_count'] == 3
    
    def test_aggregate_to_user_track_empty(self):
        """Test aggregation with empty input."""
        cues_df = pd.DataFrame(columns=['user_id', 'track_id', 'cue_id'])
        cues_metadata = pd.DataFrame(columns=['cue_id', 'vividness', 'valence'])
        
        result = aggregate_to_user_track(cues_df, cues_metadata)
        
        assert len(result) == 0

class TestFilterZeroVariance:
    """Tests for filter_zero_variance function."""
    
    def test_filter_zero_variance_basic(self):
        """Test filtering tracks with zero User-Track pairs."""
        # Create mock data
        df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'track_id': [101, 102, 102],
            'mean_vividness': [0.8, 0.6, 0.9],
            'mean_valence': [0.7, 0.5, 0.8]
        })
        
        # Track 103 has no pairs (not in dataframe)
        
        result = filter_zero_variance(df)
        
        # All tracks in the dataframe should be kept
        assert len(result) == 3
        assert set(result['track_id'].unique()) == {101, 102}
    
    def test_filter_zero_variance_with_orphans(self):
        """Test that tracks with no pairs are removed."""
        # In this function, we're filtering the dataframe itself,
        # so all rows in the dataframe are by definition pairs
        # This test verifies the function doesn't remove anything incorrectly
        
        df = pd.DataFrame({
            'user_id': [1, 2, 3, 4],
            'track_id': [101, 102, 103, 104],
            'mean_vividness': [0.8, 0.6, 0.9, 0.7],
            'mean_valence': [0.7, 0.5, 0.8, 0.6]
        })
        
        result = filter_zero_variance(df)
        
        assert len(result) == 4
        assert set(result['track_id'].unique()) == {101, 102, 103, 104}

class TestEnforceMatchRate:
    """Tests for enforce_match_rate function."""
    
    @patch('aggregation.get_config_dict')
    def test_enforce_match_rate_deferred(self, mock_config):
        """Test match rate enforcement with [deferred] threshold."""
        mock_config.return_value = {'MATCH_RATE_THRESHOLD': '[deferred]'}
        
        cues_df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'track_id': [101, 102, 103],
            'cue_id': [1, 2, 3]
        })
        
        aggregated_df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'track_id': [101, 102, 103],
            'mean_vividness': [0.8, 0.6, 0.9],
            'cue_count': [1, 1, 1]
        })
        
        result = enforce_match_rate(aggregated_df, cues_df)
        
        # Should return the same dataframe
        assert len(result) == 3
    
    @patch('aggregation.get_config_dict')
    def test_enforce_match_rate_below_threshold(self, mock_config):
        """Test match rate enforcement when below numeric threshold."""
        mock_config.return_value = {'MATCH_RATE_THRESHOLD': 0.8}
        
        cues_df = pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'track_id': [101, 102, 103, 104, 105],
            'cue_id': [1, 2, 3, 4, 5]
        })
        
        # Only 3 out of 5 cues matched (60% < 80%)
        aggregated_df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'track_id': [101, 102, 103],
            'mean_vividness': [0.8, 0.6, 0.9],
            'cue_count': [1, 1, 1]
        })
        
        result = enforce_match_rate(aggregated_df, cues_df)
        
        # Should still return the dataframe (warning logged, not exception)
        assert len(result) == 3
    
    @patch('aggregation.get_config_dict')
    def test_enforce_match_rate_above_threshold(self, mock_config):
        """Test match rate enforcement when above numeric threshold."""
        mock_config.return_value = {'MATCH_RATE_THRESHOLD': 0.5}
        
        cues_df = pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'track_id': [101, 102, 103, 104, 105],
            'cue_id': [1, 2, 3, 4, 5]
        })
        
        # 5 out of 5 cues matched (100% > 50%)
        aggregated_df = pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'track_id': [101, 102, 103, 104, 105],
            'mean_vividness': [0.8, 0.6, 0.9, 0.7, 0.5],
            'cue_count': [1, 1, 1, 1, 1]
        })
        
        result = enforce_match_rate(aggregated_df, cues_df)
        
        assert len(result) == 5
    
    @patch('aggregation.get_config_dict')
    def test_enforce_match_rate_invalid_threshold(self, mock_config):
        """Test match rate enforcement with invalid threshold value."""
        mock_config.return_value = {'MATCH_RATE_THRESHOLD': 'invalid'}
        
        cues_df = pd.DataFrame({
            'user_id': [1],
            'track_id': [101],
            'cue_id': [1]
        })
        
        aggregated_df = pd.DataFrame({
            'user_id': [1],
            'track_id': [101],
            'mean_vividness': [0.8],
            'cue_count': [1]
        })
        
        result = enforce_match_rate(aggregated_df, cues_df)
        
        assert len(result) == 1

class TestLoadAggregatedData:
    """Tests for load_aggregated_data function."""
    
    @patch('aggregation.get_project_root')
    @patch('aggregation.pd.read_parquet')
    def test_load_aggregated_data_success(self, mock_read_parquet, mock_get_root):
        """Test successful loading of aggregated data."""
        mock_get_root.return_value = Path('/mock/root')
        mock_df = pd.DataFrame({
            'user_id': [1, 2],
            'track_id': [101, 102],
            'mean_vividness': [0.8, 0.6]
        })
        mock_read_parquet.return_value = mock_df
        
        result = load_aggregated_data()
        
        assert result is not None
        assert len(result) == 2
        mock_read_parquet.assert_called_once()
    
    @patch('aggregation.get_project_root')
    def test_load_aggregated_data_file_not_found(self, mock_get_root):
        """Test loading when file doesn't exist."""
        mock_get_root.return_value = Path('/mock/root')
        
        with patch('pathlib.Path.exists', return_value=False):
            result = load_aggregated_data()
            
            assert result is None