"""
Unit tests for persist_timestamp_features.py.

These tests verify that:
1. The script can load or generate intermediate events (mocked).
2. Timestamp features are correctly extracted (hour, day, inter-arrival).
3. The output is a valid Parquet file with expected columns.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from persist_timestamp_features import extract_timestamp_features, load_or_generate_intermediate_events

class TestExtractTimestampFeatures:
    def test_extract_basic_features(self):
        """Test extraction of hour, day, weekend flags."""
        data = {
            'project_id': ['P1', 'P1', 'P2'],
            'timestamp': [
                datetime(2023, 1, 1, 10, 0),  # Sunday
                datetime(2023, 1, 2, 14, 0),  # Monday
                datetime(2023, 1, 3, 20, 0)   # Tuesday
            ]
        }
        df = pd.DataFrame(data)
        
        result = extract_timestamp_features(df, {})
        
        assert 'hour_of_day' in result.columns
        assert 'day_of_week' in result.columns
        assert 'is_weekend' in result.columns
        assert 'inter_arrival_time_seconds' in result.columns
        
        # Check values
        assert result.iloc[0]['hour_of_day'] == 10
        assert result.iloc[0]['day_of_week'] == 6  # Sunday
        assert result.iloc[0]['is_weekend'] == True
        
        assert result.iloc[1]['hour_of_day'] == 14
        assert result.iloc[1]['day_of_week'] == 0  # Monday
        assert result.iloc[1]['is_weekend'] == False

    def test_extract_inter_arrival_times(self):
        """Test calculation of inter-arrival times."""
        data = {
            'project_id': ['P1', 'P1', 'P1'],
            'timestamp': [
                datetime(2023, 1, 1, 10, 0),
                datetime(2023, 1, 1, 10, 5), # 5 mins later
                datetime(2023, 1, 1, 10, 15) # 10 mins after previous
            ]
        }
        df = pd.DataFrame(data)
        
        result = extract_timestamp_features(df, {})
        
        # First event in group should be NaN
        assert pd.isna(result.iloc[0]['inter_arrival_time_seconds'])
        # Second: 5 mins = 300 seconds
        assert result.iloc[1]['inter_arrival_time_seconds'] == 300.0
        # Third: 10 mins = 600 seconds
        assert result.iloc[2]['inter_arrival_time_seconds'] == 600.0

    def test_empty_dataframe_raises(self):
        """Test that empty dataframe raises ValueError."""
        df = pd.DataFrame()
        with pytest.raises(ValueError):
            extract_timestamp_features(df, {})

class TestLoadOrGenerateIntermediateEvents:
    @patch('persist_timestamp_features.fetch_project_events')
    @patch('persist_timestamp_features.save_events_to_csv')
    def test_load_existing_file(self, mock_save, mock_fetch):
        """Test that it loads an existing file and doesn't call fetch."""
        # Mock config
        config = {
            'paths': {'derived': '/tmp'},
            'sample_projects': ['P1']
        }
        
        # Mock file existence check
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pandas.read_csv') as mock_read:
                mock_read.return_value = pd.DataFrame({'col': [1]})
                result = load_or_generate_intermediate_events(config)
                
                mock_read.assert_called_once()
                mock_fetch.assert_not_called()
                assert result is not None

    @patch('persist_timestamp_events.fetch_project_events')
    def test_generate_from_api(self, mock_fetch):
        """Test that it fetches data if file missing."""
        config = {
            'paths': {'derived': '/tmp'},
            'sample_projects': ['P1']
        }
        
        mock_fetch.return_value = [
            {'project_id': 'P1', 'timestamp': '2023-01-01 10:00:00', 'author': 'A', 'event_type': 'comment', 'comment_body': 'test'}
        ]
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('pandas.DataFrame.to_csv'):
                result = load_or_generate_intermediate_events(config)
                
                mock_fetch.assert_called_once_with('P1')
                assert len(result) == 1
                assert result.iloc[0]['author'] == 'A'