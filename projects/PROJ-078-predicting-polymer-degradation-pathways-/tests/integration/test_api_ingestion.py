"""Integration tests for API ingestion with rate-limit backoff."""
import pytest
import time
from unittest.mock import patch, MagicMock, call
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import enforce_rate_limit, download_records_from_nist
from utils import get_logger

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock = MagicMock()
    return mock

def test_backoff_on_rate_limit(mock_logger):
    """Test that rate limit backoff is enforced correctly."""
    # Mock the rate limit enforcement
    with patch('ingest.time.sleep') as mock_sleep:
        # Simulate rate limit scenario: last request was 0.1s ago, min interval is 1.0s
        # This should trigger a sleep of 0.9s
        start_time = time.time()
        
        enforce_rate_limit(last_request_time=time.time() - 0.1, 
                         min_interval=1.0, 
                         logger=mock_logger)
        
        # Verify that sleep was called due to rate limiting
        assert mock_sleep.called
        # Verify the sleep duration is approximately correct (allowing for float precision)
        mock_sleep.assert_called_once()
        sleep_duration = mock_sleep.call_args[0][0]
        assert 0.8 < sleep_duration < 1.0  # Should be around 0.9s
        
        # Verify the logger was called with backoff info
        assert mock_logger.warning.called
        # Check that the warning message contains relevant info
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Rate limit" in warning_call or "backoff" in warning_call.lower()

def test_no_backoff_when_within_limits(mock_logger):
    """Test that no backoff occurs when within rate limits."""
    with patch('ingest.time.sleep') as mock_sleep:
        # Simulate scenario within rate limits: last request was 2.0s ago, min interval is 1.0s
        enforce_rate_limit(last_request_time=time.time() - 2.0, 
                         min_interval=1.0, 
                         logger=mock_logger)
        
        # Verify that sleep was NOT called
        assert not mock_sleep.called
        
        # Verify that the logger was NOT called with a warning
        assert not mock_logger.warning.called

def test_download_records_with_rate_limiting(mock_logger):
    """Test that record download respects rate limiting."""
    # Mock the API response
    mock_response_data = {
        'result': {
            'record': [
                {'Name': 'Ethanol', 'ID': '64-17-5'},
                {'Name': 'Acetic Acid', 'ID': '64-19-7'}
            ]
        }
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    
    with patch('ingest.requests.get') as mock_get:
        mock_get.return_value = mock_response
        
        with patch('ingest.time.sleep') as mock_sleep:
            # Attempt to download records
            # Using a small list to ensure we test multiple calls
            smiles_list = ['CCO', 'CC(=O)O']
            results = download_records_from_nist(
                smiles_list=smiles_list,
                logger=mock_logger,
                max_retries=3
            )
            
            # Verify that requests were made (once per SMILES)
            assert mock_get.call_count == len(smiles_list)
            
            # Verify that sleep was called between requests (rate limiting)
            # We expect at least (n-1) sleeps for n requests
            assert mock_sleep.call_count >= len(smiles_list) - 1
            
            # Verify results were returned
            assert len(results) == len(smiles_list)
            
            # Verify that each result contains expected keys
            for result in results:
                assert 'smiles' in result or 'id' in result

def test_rate_limit_retry_logic(mock_logger):
    """Test that the rate limit backoff handles retries correctly."""
    # Mock a scenario where the first request fails with 429 (rate limit)
    # and the second succeeds
    
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {
        'result': {'record': [{'Name': 'Test', 'ID': '123'}]}
    }
    
    # First call returns 429, second call returns 200
    mock_get = MagicMock()
    mock_get.side_effect = [mock_response_429, mock_response_200]
    
    with patch('ingest.requests.get', mock_get):
        with patch('ingest.time.sleep') as mock_sleep:
            results = download_records_from_nist(
                smiles_list=['CCO'],
                logger=mock_logger,
                max_retries=3
            )
            
            # Verify that requests were made twice (first failed, second succeeded)
            assert mock_get.call_count == 2
            
            # Verify that sleep was called after the 429 response
            assert mock_sleep.called
            
            # Verify results were eventually returned
            assert len(results) == 1