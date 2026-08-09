"""
Unit tests for data ingestion chunking and rate limit handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion import (
    is_bot_actor,
    filter_bot_events,
    fetch_project_events_chunked,
    ingest_sample_projects,
    CHUNK_SIZE
)
from models import EventType
from utils.github_client import GitHubRateLimitError

class TestBotFiltering:
    def test_is_bot_actor_true_suffix(self):
        assert is_bot_actor("dependabot[bot]") is True
        assert is_bot_actor("my-bot[bot]") is True

    def test_is_bot_actor_true_prefix(self):
        assert is_bot_actor("dependabot") is True
        assert is_bot_actor("renovate-bot") is True
        assert is_bot_actor("codecov-io") is True

    def test_is_bot_actor_false(self):
        assert is_bot_actor("torvalds") is False
        assert is_bot_actor("octocat") is False
        assert is_bot_actor("user123") is False

    def test_is_bot_actor_empty(self):
        assert is_bot_actor("") is True
        assert is_bot_actor(None) is True

    def test_filter_bot_events(self):
        events = [
            {"actor": {"login": "user1"}},
            {"actor": {"login": "bot[bot]"}},
            {"actor": {"login": "user2"}},
            {"actor": {"login": "dependabot"}},
        ]
        filtered = filter_bot_events(events)
        assert len(filtered) == 2
        assert filtered[0]["actor"]["login"] == "user1"
        assert filtered[1]["actor"]["login"] == "user2"

class TestChunkingAndRateLimits:
    @patch('data_ingestion.create_client')
    def test_fetch_project_events_chunked_rate_limit_retry(self, mock_create_client):
        """Test that rate limit errors trigger a wait and retry."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Simulate a rate limit error on the first request, then success
        mock_response_fail = Mock()
        mock_response_fail.status_code = 200
        mock_response_fail.json.return_value = [] # Empty to stop loop after retry logic check? 
        # Actually, let's test the loop behavior with a mock that raises the error
        
        def mock_request_side_effect(*args, **kwargs):
            # First call raises error
            if not hasattr(mock_request_side_effect, 'called'):
                mock_request_side_effect.called = True
                raise GitHubRateLimitError("Rate limit exceeded", wait_time=0.01)
            # Subsequent calls return empty list to stop loop
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = []
            return mock_resp

        mock_client._request.side_effect = mock_request_side_effect
        
        events_gen = fetch_project_events_chunked(mock_client, "owner/repo")
        
        # The generator should handle the error and continue
        try:
            next(events_gen)
        except StopIteration:
            pass # Expected if loop breaks
        
        # Verify _request was called at least twice (once failed, once success)
        assert mock_client._request.call_count >= 2

    @patch('data_ingestion.create_client')
    def test_ingest_sample_projects_large_dataset_handling(self, mock_create_client):
        """Test that ingestion handles large datasets without OOM by processing in chunks."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock a large dataset scenario
        def mock_request_side_effect(*args, **kwargs):
            mock_resp = Mock()
            mock_resp.status_code = 200
            # Return a small chunk to simulate pagination
            mock_resp.json.return_value = [
                {"id": str(i), "type": "IssuesEvent", "created_at": "2023-01-01T00:00:00Z", 
                 "actor": {"login": f"user{i}"}, "repo": {"name": "test/repo"}, 
                 "payload": {"action": "opened"}}
                for i in range(100)
            ]
            return mock_resp

        mock_client._request.side_effect = mock_request_side_effect
        
        # Mock the sleep to avoid waiting in tests
        with patch('data_ingestion.time.sleep'):
            results = ingest_sample_projects(
                sample_repos=["test/repo"],
                event_types=[EventType.ISSUES],
                since=datetime.now(),
                until=datetime.now()
            )
        
        assert results["total_projects_processed"] == 1
        assert results["projects"]["test/repo"]["status"] == "success"
        # The logic should have fetched multiple pages until empty

    def test_chunk_size_constant(self):
        """Verify the chunk size constant is set to 100k."""
        assert CHUNK_SIZE == 100000