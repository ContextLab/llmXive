"""
Unit tests for data ingestion and filtering logic.
"""
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from code.data_ingestion import filter_insufficient_data, filter_bots
from code.models import Event, ContributorPair

class TestFilterBots:
    def test_filter_bots_removes_bot_events(self):
        events = [
            {'author': 'user1', 'is_bot': False},
            {'author': 'dependabot[bot]', 'is_bot': True},
            {'author': 'user2', 'is_bot': False},
            {'author': 'github-actions[bot]', 'is_bot': True}
        ]
        
        result = filter_bots(events)
        
        assert len(result) == 2
        assert all(not e['is_bot'] for e in result)
        assert result[0]['author'] == 'user1'
        assert result[1]['author'] == 'user2'

    def test_filter_bots_empty_list(self):
        result = filter_bots([])
        assert result == []

class TestFilterInsufficientData:
    def test_filter_removes_low_count_projects(self):
        projects = [
            {'repo': 'high-data', 'event_count': 100},
            {'repo': 'low-data', 'event_count': 5},
            {'repo': 'boundary', 'event_count': 10}
        ]
        
        # Mock config to set min_events to 10
        with patch('code.data_ingestion.get_config') as mock_config:
            mock_config.return_value = {'min_events': 10}
            result = filter_insufficient_data(projects)
        
        assert len(result) == 2
        repos = [p['repo'] for p in result]
        assert 'high-data' in repos
        assert 'boundary' in repos
        assert 'low-data' not in repos

    def test_filter_keeps_all_above_threshold(self):
        projects = [
            {'repo': 'proj1', 'event_count': 20},
            {'repo': 'proj2', 'event_count': 30}
        ]
        
        with patch('code.data_ingestion.get_config') as mock_config:
            mock_config.return_value = {'min_events': 10}
            result = filter_insufficient_data(projects)
        
        assert len(result) == 2

    def test_filter_removes_all_below_threshold(self):
        projects = [
            {'repo': 'proj1', 'event_count': 2},
            {'repo': 'proj2', 'event_count': 5}
        ]
        
        with patch('code.data_ingestion.get_config') as mock_config:
            mock_config.return_value = {'min_events': 10}
            result = filter_insufficient_data(projects)
        
        assert len(result) == 0

    def test_filter_default_threshold(self):
        projects = [
            {'repo': 'proj1', 'event_count': 9},
            {'repo': 'proj2', 'event_count': 10}
        ]
        
        # Test with default min_events (10)
        with patch('code.data_ingestion.get_config') as mock_config:
            mock_config.return_value = {} # No min_events key
            result = filter_insufficient_data(projects)
        
        assert len(result) == 1
        assert result[0]['repo'] == 'proj2'