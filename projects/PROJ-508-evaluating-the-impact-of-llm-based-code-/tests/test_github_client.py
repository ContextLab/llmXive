"""
Tests for the GitHub client retry logic and basic functionality.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock, call
from utils.github_client import GitHubClient

@pytest.fixture
def github_client():
    return GitHubClient(token="fake_token")

@patch('utils.github_client.requests.get')
def test_successful_request(mock_get, github_client):
    """Test a successful API request."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    result = github_client._request("https://api.github.com/repos/test")
    assert result == {"data": "test"}
    mock_get.assert_called_once()

@patch('utils.github_client.requests.get')
def test_retry_on_connection_error(mock_get, github_client):
    """Test that the client retries on connection errors with exponential backoff."""
    # Simulate 2 failures then success
    mock_get.side_effect = [
        requests.exceptions.ConnectionError("Timeout"),
        requests.exceptions.ConnectionError("Timeout"),
        MagicMock(status_code=200, json=lambda: {"data": "success"})
    ]

    result = github_client._request("https://api.github.com/repos/test")
    assert result == {"data": "success"}
    # Should have called 3 times (2 retries + 1 success)
    assert mock_get.call_count == 3

@patch('utils.github_client.requests.get')
def test_retry_limit_exceeded(mock_get, github_client):
    """Test that the client raises after max retries."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Timeout")

    with pytest.raises(requests.exceptions.ConnectionError):
        github_client._request("https://api.github.com/repos/test")

@patch('utils.github_client.requests.get')
def test_retry_on_500_status(mock_get, github_client):
    """Test that the client retries on 500 status codes."""
    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"data": "ok"}

    mock_get.side_effect = [
        mock_response_500,
        mock_response_500,
        mock_response_200
    ]

    result = github_client._request("https://api.github.com/repos/test")
    assert result == {"data": "ok"}
    assert mock_get.call_count == 3

@patch('utils.github_client.requests.get')
def test_no_retry_on_404(mock_get, github_client):
    """Test that the client does NOT retry on 404 errors."""
    mock_response_404 = MagicMock()
    mock_response_404.status_code = 404
    mock_response_404.json.return_value = {"message": "Not Found"}
    mock_get.return_value = mock_response_404

    result = github_client._request("https://api.github.com/repos/test")
    # Should raise HTTPError or return the response depending on implementation
    # Based on typical retry logic, 4xx are usually not retried
    assert mock_get.call_count == 1

@patch('utils.github_client.time.sleep')
@patch('utils.github_client.requests.get')
def test_exponential_backoff_delays(mock_get, mock_sleep, github_client):
    """Test that retry delays follow exponential backoff pattern."""
    mock_get.side_effect = [
        requests.exceptions.ConnectionError("Timeout"),
        requests.exceptions.ConnectionError("Timeout"),
        MagicMock(status_code=200, json=lambda: {"data": "success"})
    ]

    result = github_client._request("https://api.github.com/repos/test")
    assert result == {"data": "success"}
    
    # Verify sleep was called with increasing delays (base * 2^attempt)
    # Assuming base delay is 1 second and max attempts is 3
    # Calls should be: 1s, 2s (or similar exponential pattern)
    assert mock_sleep.call_count == 2
    # Check that delays are increasing (first call < second call)
    first_delay = mock_sleep.call_args_list[0][0][0]
    second_delay = mock_sleep.call_args_list[1][0][0]
    assert second_delay >= first_delay