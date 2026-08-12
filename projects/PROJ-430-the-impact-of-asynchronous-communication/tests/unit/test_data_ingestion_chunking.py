import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_ingestion import fetch_project_events_chunked, log_rate_limit_event
from config import get_config

@pytest.fixture
def mock_client():
    """Create a mock GitHubClient."""
    client = MagicMock()
    # Mock the get_events method to return paginated data
    def mock_get_events(repo_id, page=1, per_page=100):
        if page > 2:
            return []
        # Return a list of events with a unique ID per page
        return [{'id': f'{repo_id}-{page}-{i}', 'actor': {'login': f'user{i}', 'type': 'User'}} for i in range(per_page)]
    client.get_events = mock_get_events
    return client

def test_fetch_chunking_large_dataset(mock_client):
    """Test that events are yielded in chunks when dataset is large."""
    repo_id = 12345
    chunk_size = 50  # Small chunk size for testing
    
    # Patch the CHUNK_SIZE constant
    with patch('data_ingestion.CHUNK_SIZE', chunk_size):
        chunks = list(fetch_project_events_chunked(repo_id, mock_client))
    
    # Verify we got chunks
    assert len(chunks) > 0
    # Verify each chunk (except possibly the last) is <= chunk_size
    for chunk in chunks[:-1]:
        assert len(chunk) <= chunk_size

def test_rate_limit_logging(tmp_path):
    """Test that rate limit events are logged correctly."""
    # Mock config to use temp directory
    with patch('data_ingestion.get_config') as mock_config:
        mock_config.return_value = {
            'data_dir': tmp_path,
            'raw_dir': tmp_path / 'raw',
            'logs_dir': tmp_path / 'logs'
        }
        with patch('data_ingestion.ensure_directories_exist'):
            log_rate_limit_event(12345, "Rate limit exceeded")
    
    log_file = tmp_path / 'logs' / 'rate_limit_events.log'
    assert log_file.exists()
    with open(log_file, 'r') as f:
        content = f.read()
    assert "12345" in content
    assert "Rate limit exceeded" in content

def test_fetch_with_rate_limit_error(mock_client):
    """Test handling of rate limit errors during fetch."""
    from data_ingestion import GitHubRateLimitError
    
    # Create a client that raises rate limit error on first call
    def mock_get_events_with_error(repo_id, page=1, per_page=100):
        if page == 1:
            raise GitHubRateLimitError("Rate limit exceeded")
        return [{'id': f'{repo_id}-{page}-{i}', 'actor': {'login': f'user{i}', 'type': 'User'}} for i in range(per_page)]
    
    mock_client.get_events = mock_get_events_with_error
    
    # Should retry and succeed
    chunks = list(fetch_project_events_chunked(12345, mock_client))
    assert len(chunks) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])