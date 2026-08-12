"""
Unit tests for metrics calculation module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from metrics import (
    is_bot_actor,
    identify_pairs_and_calculate_metrics,
    calculate_and_persist_pair_metrics,
    calculate_project_level_metrics
)


class TestIsBotActor:
    def test_bot_by_name(self):
        assert is_bot_actor('github-actions[bot]') is True
        assert is_bot_actor('dependabot[bot]') is True
        
    def test_bot_by_type(self):
        assert is_bot_actor('someuser', 'Bot') is True
        
    def test_not_bot(self):
        assert is_bot_actor('alice') is False
        assert is_bot_actor('alice', 'User') is False
        
    def test_empty_login(self):
        assert is_bot_actor('') is False
        assert is_bot_actor(None) is False


class TestIdentifyPairsAndCalculateMetrics:
    def test_basic_pair_calculation(self):
        events = [
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:00:00Z',
                'text': 'Hello'
            },
            {
                'project_id': '12345',
                'author_id': 'user2',
                'timestamp': '2023-01-01T10:05:00Z',
                'text': 'Hi'
            },
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:15:00Z',
                'text': 'How are you?'
            },
            {
                'project_id': '12345',
                'author_id': 'user2',
                'timestamp': '2023-01-01T10:20:00Z',
                'text': 'Good!'
            }
        ]
        
        metrics = identify_pairs_and_calculate_metrics(events)
        
        assert len(metrics) >= 1
        assert all('project_id' in m for m in metrics)
        assert all('pair_id' in m for m in metrics)
        assert all('response_time_variance' in m for m in metrics)
        assert all('mean_delay' in m for m in metrics)
        assert all('pair_count' in m for m in metrics)
        
        # Check that variance and mean_delay are non-negative
        for m in metrics:
            assert m['response_time_variance'] >= 0
            assert m['mean_delay'] >= 0
            
    def test_bot_exclusion(self):
        events = [
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:00:00Z',
                'text': 'Hello'
            },
            {
                'project_id': '12345',
                'author_id': 'bot[bot]',
                'timestamp': '2023-01-01T10:05:00Z',
                'text': 'Bot message'
            },
            {
                'project_id': '12345',
                'author_id': 'user2',
                'timestamp': '2023-01-01T10:10:00Z',
                'text': 'Hi'
            }
        ]
        
        metrics = identify_pairs_and_calculate_metrics(events)
        
        # Should only have user1-user2 pair, not involving the bot
        pair_ids = [m['pair_id'] for m in metrics]
        assert not any('bot' in str(pid) for pid in pair_ids)
        
    def test_single_event_no_metrics(self):
        events = [
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:00:00Z',
                'text': 'Hello'
            }
        ]
        
        metrics = identify_pairs_and_calculate_metrics(events)
        assert len(metrics) == 0
        
    def test_multiple_projects(self):
        events = [
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:00:00Z',
                'text': 'Hello'
            },
            {
                'project_id': '12345',
                'author_id': 'user2',
                'timestamp': '2023-01-01T10:05:00Z',
                'text': 'Hi'
            },
            {
                'project_id': '67890',
                'author_id': 'user3',
                'timestamp': '2023-01-01T10:00:00Z',
                'text': 'Project 2'
            },
            {
                'project_id': '67890',
                'author_id': 'user4',
                'timestamp': '2023-01-01T10:10:00Z',
                'text': 'Reply'
            }
        ]
        
        metrics = identify_pairs_and_calculate_metrics(events)
        
        project_ids = set(m['project_id'] for m in metrics)
        assert '12345' in project_ids
        assert '67890' in project_ids


class TestCalculateAndPersistPairMetrics:
    def test_persist_to_parquet(self):
        events = [
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:00:00Z',
                'text': 'Hello'
            },
            {
                'project_id': '12345',
                'author_id': 'user2',
                'timestamp': '2023-01-01T10:05:00Z',
                'text': 'Hi'
            },
            {
                'project_id': '12345',
                'author_id': 'user1',
                'timestamp': '2023-01-01T10:15:00Z',
                'text': 'How are you?'
            },
            {
                'project_id': '12345',
                'author_id': 'user2',
                'timestamp': '2023-01-01T10:20:00Z',
                'text': 'Good!'
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_metrics.parquet')
            result = calculate_and_persist_pair_metrics(events, output_path)
            
            assert os.path.exists(result)
            assert result == output_path
            
            # Verify parquet file can be read
            df = pd.read_parquet(output_path)
            assert len(df) > 0
            assert 'response_time_variance' in df.columns
            assert 'mean_delay' in df.columns
            assert 'pair_id' in df.columns
            
            # Check no NaN in critical columns
            assert not df['response_time_variance'].isna().any()
            assert not df['mean_delay'].isna().any()
            
    def test_empty_events_creates_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'empty_metrics.parquet')
            result = calculate_and_persist_pair_metrics([], output_path)
            
            assert os.path.exists(result)
            df = pd.read_parquet(output_path)
            assert len(df) == 0
            assert 'response_time_variance' in df.columns


class TestCalculateProjectLevelMetrics:
    def test_aggregation(self):
        pair_metrics = [
            {
                'project_id': '12345',
                'pair_id': "('user1', 'user2')",
                'response_time_variance': 10.0,
                'mean_delay': 300.0,
                'pair_count': 5
            },
            {
                'project_id': '12345',
                'pair_id': "('user1', 'user3')",
                'response_time_variance': 20.0,
                'mean_delay': 400.0,
                'pair_count': 3
            },
            {
                'project_id': '67890',
                'pair_id': "('user4', 'user5')",
                'response_time_variance': 15.0,
                'mean_delay': 350.0,
                'pair_count': 4
            }
        ]
        
        project_metrics = calculate_project_level_metrics(pair_metrics)
        
        assert len(project_metrics) == 2
        
        # Find metrics for project 12345
        proj_12345 = next(m for m in project_metrics if m['project_id'] == '12345')
        
        # Median of [10, 20] is 15
        assert proj_12345['median_variance'] == 15.0
        assert proj_12345['pair_count'] == 2