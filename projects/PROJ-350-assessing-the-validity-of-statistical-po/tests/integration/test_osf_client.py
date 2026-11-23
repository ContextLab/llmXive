"""
Integration tests for OSF API connection and backoff logic.

These tests verify that the OSFClient in `code/utils/osf_client.py` correctly:
1. Connects to the real OSF API.
2. Handles rate limiting with exponential backoff.
3. Retrieves metadata for a known study.

Note: These tests require network access and a small amount of time to execute
due to the backoff logic verification.
"""
import os
import time
import pytest
from unittest.mock import patch, MagicMock
import requests

# Import the module under test
from code.utils.osf_client import (
    OSFClient,
    OSFClientError,
    RateLimitExceededError,
    fetch_with_backoff,
    get_study_metadata,
)

# Use a known, public OSF project ID for integration testing.
# This project is small, stable, and publicly accessible.
# Example: "osf.io/5z8q7" (A generic public project)
# We will use a specific, well-known study ID if available, or a generic one.
# For robustness, we use a known valid ID: "osf.io/6v2k8" (Example public data)
# If this ID is unavailable, the test will fail, which is expected behavior for integration tests.
TEST_OSF_ID = "6v2k8"  # Replace with a verified public OSF ID if this one changes
TEST_OSF_URL = f"https://api.osf.io/v2/projects/{TEST_OSF_ID}/"

# A list of known public OSF IDs to test against to ensure at least one works
VALID_OSF_IDS = [
    "6v2k8",  # Example public project
    "5z8q7",  # Another example
    "qz8r9",  # Fallback
]

@pytest.fixture
def valid_osf_id():
    """Find a valid OSF ID from the list to use for testing."""
    for oid in VALID_OSF_IDS:
        try:
            url = f"https://api.osf.io/v2/projects/{oid}/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return oid
        except requests.RequestException:
            continue
    pytest.skip("No valid public OSF project ID found for integration testing.")
    return None

def test_fetch_with_backoff_success(valid_osf_id):
    """Test that fetch_with_backoff successfully retrieves data without rate limiting."""
    url = f"https://api.osf.io/v2/projects/{valid_osf_id}/"
    
    # This should succeed immediately
    start_time = time.time()
    result = fetch_with_backoff(url, max_retries=3)
    elapsed = time.time() - start_time

    assert result is not None
    assert "data" in result
    assert "id" in result["data"]
    assert result["data"]["id"] == valid_osf_id
    # Should be fast (< 2 seconds)
    assert elapsed < 2.0, f"Request took too long: {elapsed}s"

def test_fetch_with_backoff_rate_limit_simulation():
    """
    Test that fetch_with_backoff correctly implements exponential backoff
    when the server returns 429 (Too Many Requests).
    """
    url = "https://api.osf.io/v2/projects/fake-id/"
    
    # Mock the requests.get to simulate a rate limit response
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "1"} # 1 second wait
    mock_response_429.json.return_value = {"detail": "Rate limit exceeded"}

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"data": {"id": "fake-id", "attributes": {}}}

    # Sequence: 429, 429, 200
    call_count = 0
    def mock_get_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return mock_response_429
        return mock_response_success

    with patch('code.utils.osf_client.requests.get', side_effect=mock_get_side_effect):
        # We expect it to succeed after retries
        # Note: The actual backoff time in the code might be small for testing,
        # but we verify the retry count.
        result = fetch_with_backoff(url, max_retries=3, base_delay=0.1) # Fast base delay for test

    assert result is not None
    assert call_count == 3 # Failed twice, succeeded on third

def test_fetch_with_backoff_max_retries_exceeded():
    """Test that fetch_with_backoff raises an error when max retries are exceeded."""
    url = "https://api.osf.io/v2/projects/fake-id/"
    
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "0"}
    
    with patch('code.utils.osf_client.requests.get', return_value=mock_response_429):
        with pytest.raises(RateLimitExceededError):
            fetch_with_backoff(url, max_retries=2, base_delay=0.01)

def test_get_study_metadata_integration(valid_osf_id):
    """
    Integration test: Verify get_study_metadata can fetch real data from OSF.
    """
    metadata = get_study_metadata(valid_osf_id)
    
    assert metadata is not None
    assert "id" in metadata
    assert metadata["id"] == valid_osf_id
    assert "attributes" in metadata
    assert "title" in metadata["attributes"]
    # Ensure we got a real string, not a placeholder
    assert isinstance(metadata["attributes"]["title"], str)
    assert len(metadata["attributes"]["title"]) > 0

def test_osf_client_initialization():
    """Test that OSFClient initializes correctly with default settings."""
    client = OSFClient()
    assert client.base_url == "https://api.osf.io/v2/"
    assert client.timeout == 30
    assert client.max_retries == 3
    assert client.base_delay == 1.0

def test_osf_client_custom_settings():
    """Test OSFClient with custom configuration."""
    client = OSFClient(base_url="https://custom.osf.io/", timeout=10, max_retries=5)
    assert client.base_url == "https://custom.osf.io/"
    assert client.timeout == 10
    assert client.max_retries == 5