"""Integration tests for API ingestion with rate-limit backoff."""
import pytest
import time
from unittest.mock import patch, MagicMock
from ingest import enforce_rate_limit, download_records_from_nist

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    mock = MagicMock()
    return mock

def test_backoff_on_rate_limit(mock_logger):
    """Test that rate limit backoff is enforced correctly."""
    # Mock the rate limit enforcement
    with patch('ingest.time.sleep') as mock_sleep:
        # Simulate rate limit scenario
        start_time = time.time()
        
        # Call the rate limit enforcement
        # This should trigger backoff logic
        enforce_rate_limit(last_request_time=time.time() - 0.1, 
                         min_interval=1.0, 
                         logger=mock_logger)
        
        # Verify that sleep was called due to rate limiting
        assert mock_sleep.called
        
        # Verify the logger was called with backoff info
        assert mock_logger.warning.called

def test_no_backoff_when_within_limits(mock_logger):
    """Test that no backoff occurs when within rate limits."""
    with patch('ingest.time.sleep') as mock_sleep:
        # Simulate scenario within rate limits
        enforce_rate_limit(last_request_time=time.time() - 2.0, 
                         min_interval=1.0, 
                         logger=mock_logger)
        
        # Verify that sleep was NOT called
        assert not mock_sleep.called

def test_download_records_with_rate_limiting(mock_logger):
    """Test that record download respects rate limiting."""
    # Mock the API response
    mock_response = {
        'status': 'success',
        'data': [{'smiles': 'CCO', 'pathway': 'hydrolysis'}]
    }
    
    with patch('ingest.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        with patch('ingest.time.sleep') as mock_sleep:
            # Attempt to download records
            results = download_records_from_nist(
                smiles_list=['CCO', 'CC(=O)O'],
                logger=mock_logger,
                max_retries=3
            )
            
            # Verify that requests were made
            assert mock_get.called
            
            # Verify results were returned
            assert len(results) > 0
