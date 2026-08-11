"""
Unit tests for T016: Error handling for API rate limits and large datasets (chunking).

Verifies:
1. is_bot_actor correctly identifies bots.
2. filter_bot_events removes bot events.
3. fetch_project_events_chunked yields chunks and handles rate limits.
4. Memory management logic (thresholds) is respected.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_ingestion import is_bot_actor, filter_bot_events, fetch_project_events_chunked, ingest_sample_projects
from code.utils.github_client import GitHubRateLimitError, GitHubClient
from code.models import Event

class TestBotFiltering:
    def test_is_bot_actor_login_suffix(self):
        """Test detection of [bot] suffix in login."""
        assert is_bot_actor({'login': 'dependabot[bot]'}) is True
        assert is_bot_actor({'login': 'github-actions[bot]'}) is True
        assert is_bot_actor({'login': 'regular-user'}) is False
        assert is_bot_actor({'login': 'bot'}) is False  # Just "bot" without suffix is not a bot by this rule

    def test_is_bot_actor_type_bot(self):
        """Test detection of type 'Bot'."""
        assert is_bot_actor({'type': 'Bot'}) is True
        assert is_bot_actor({'type': 'User'}) is False
        assert is_bot_actor({'type': 'bot'}) is True  # Case insensitive

    def test_is_bot_actor_empty_data(self):
        """Test handling of empty or missing data."""
        assert is_bot_actor({}) is False
        assert is_bot_actor(None) is False
        assert is_bot_actor({'login': None}) is False

    def test_filter_bot_events(self):
        """Test that filter_bot_events removes bot events."""
        events = [
            {'actor': {'login': 'user1', 'type': 'User'}},
            {'actor': {'login': 'bot-user[bot]', 'type': 'Bot'}},
            {'actor': {'login': 'user2', 'type': 'User'}},
            {'actor': {'type': 'Bot'}}, # No login, but type is Bot
        ]
        
        filtered = filter_bot_events(events)
        
        assert len(filtered) == 2
        assert filtered[0]['actor']['login'] == 'user1'
        assert filtered[1]['actor']['login'] == 'user2'

class TestChunkedFetching:
    @pytest.fixture
    def mock_client(self):
        client = Mock(spec=GitHubClient)
        return client

    def test_fetch_yields_chunks(self, mock_client):
        """Test that fetch_project_events_chunked yields lists of events."""
        mock_client.get_events.return_value = [
            {'id': 1, 'actor': {'login': 'u1'}},
            {'id': 2, 'actor': {'login': 'u2'}},
        ]
        
        generator = fetch_project_events_chunked(mock_client, 'test/repo', chunk_size=100)
        chunks = list(generator)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 2

    def test_fetch_stops_at_threshold(self, mock_client):
        """Test that fetching stops if total events exceed MAX_EVENTS_THRESHOLD."""
        # Mock to return 100k+ events over multiple pages
        def mock_get_events(*args, **kwargs):
            return [{'id': i, 'actor': {'login': 'u'}} for i in range(100100)]
        
        mock_client.get_events = mock_get_events
        
        # This should stop after hitting the threshold inside the generator
        # We expect it to yield at least one chunk, then stop
        generator = fetch_project_events_chunked(mock_client, 'test/repo', chunk_size=100)
        chunks = list(generator)
        
        # The generator logic checks total_fetched. 
        # Since we return 100100 in one call (simulating a very large page or first call),
        # it should detect the threshold and stop.
        # Note: In a real scenario, get_events returns max 100 per page.
        # Here we simulate a scenario where the check logic is triggered.
        # If the mock returns > 100k in the first chunk, the loop breaks immediately after yield.
        assert len(chunks) >= 1
        total_events = sum(len(c) for c in chunks)
        # Should be close to threshold but not exceed it significantly if logic is correct
        # Actually, the logic: total_fetched += len(events); yield; check threshold.
        # So it yields the chunk that pushes it over, then breaks.
        assert total_events >= 100000 

    def test_rate_limit_retry(self, mock_client):
        """Test that rate limit errors cause a retry."""
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise GitHubRateLimitError("Rate limit exceeded")
            return [{'id': 1, 'actor': {'login': 'u'}}]
        
        mock_client.get_events.side_effect = side_effect
        
        # Patch time.sleep to avoid actual waiting
        with patch('code.data_ingestion.time.sleep') as mock_sleep:
            generator = fetch_project_events_chunked(mock_client, 'test/repo')
            chunks = list(generator)
            
            assert call_count == 2  # First fail, second success
            mock_sleep.assert_called_once()
            assert len(chunks) == 1

class TestIngestSampleProjects:
    @patch('code.data_ingestion.GitHubClient')
    @patch('code.data_ingestion.ensure_directories_exist')
    @patch('code.data_ingestion.get_config')
    def test_ingest_handles_errors_gracefully(self, mock_config, mock_ensure, mock_client_class):
        """Test that ingest_sample_projects continues if one project fails."""
        mock_config.return_value = {
            'github_token': 'fake_token',
            'raw_events_path': '/tmp/test_events.json'
        }
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # First project fails, second succeeds
        mock_client.get_events.side_effect = [
            Exception("API Error"), # Project 1
            [{'id': 1, 'actor': {'login': 'u'}}] # Project 2
        ]
        
        stats = ingest_sample_projects(['proj1', 'proj2'], '/tmp/test_events.json')
        
        assert stats['projects_processed'] == 1
        assert len(stats['errors']) == 1
        assert 'proj1' in stats['errors'][0]
        
        # Verify output file was created with the successful data
        assert os.path.exists('/tmp/test_events.json')
        with open('/tmp/test_events.json', 'r') as f:
            data = json.load(f)
            assert len(data) == 1
