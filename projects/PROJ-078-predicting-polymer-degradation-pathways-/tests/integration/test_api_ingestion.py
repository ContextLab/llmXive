"""
Integration tests for API ingestion and rate limiting.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from ingest import enforce_rate_limit, download_records_from_nist

def test_backoff_on_rate_limit():
    """Test that rate limit backoff is enforced."""
    call_times = []
    
    @enforce_rate_limit(max_calls=2, period=1.0)
    def mock_fetch():
        call_times.append(time.time())
        return {"status": "ok"}
    
    # First two calls should succeed immediately
    mock_fetch()
    mock_fetch()
    
    # Third call should wait
    start = time.time()
    mock_fetch()
    elapsed = time.time() - start
    
    assert elapsed >= 0.9  # Allow small timing variance
    assert len(call_times) == 3

@patch('ingest.requests.get')
def test_download_records_from_nist(mock_get):
    """Test NIST record download with mocked response."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"id": "NIST001", "smiles": "CC(=O)OC", "degradation": "hydrolysis"}
        ]
    }
    mock_get.return_value = mock_response
    
    # Execute
    records = download_records_from_nist(["NIST001"])
    
    # Verify
    assert len(records) == 1
    assert records[0]["id"] == "NIST001"
    mock_get.assert_called_once()
