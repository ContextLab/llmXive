"""
Unit tests for the OpenML API client, specifically focusing on retry logic.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock
import time

# Import the client class
import sys
import os
# Ensure code/utils is in path if running from root, though typically pytest handles this via conftest or PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.api_client import OpenMLClient


class TestAPIClientRetry:
    """Tests for the retry logic in OpenMLClient."""

    @patch('code.utils.api_client.requests.Session')
    def test_api_client_retry_on_429(self, mock_session_class):
        """
        Validates that the client retries when receiving HTTP 429.
        Uses a mock session to simulate the retry behavior without hitting the network.
        """
        # Setup mock response sequence:
        # 1. First call returns 429
        # 2. Second call returns 200 with data
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"datasets": [{"id": 1, "name": "test"}]}
        mock_response_200.raise_for_status.return_value = None

        # Create a mock session instance
        mock_session_instance = MagicMock()
        mock_session_class.return_value = mock_session_instance
        
        # Configure side_effect to yield 429 then 200
        # The Retry logic in the adapter handles the loop, but we need to ensure the session.get
        # is called multiple times if we were testing the adapter directly.
        # However, since we are mocking the Session class, we need to verify the behavior
        # by checking if the underlying logic (via the adapter) would retry.
        
        # A more direct test for the Retry logic configured in the adapter:
        # We can inspect the adapter's max_retries configuration or simulate the flow.
        # Since the Retry logic is internal to the adapter, we verify that the client
        # is configured with a Retry strategy that includes 429.
        
        client = OpenMLClient(max_retries=3, backoff_factor=0.1)
        
        # Verify the adapter is mounted and configured
        http_adapter = client.session.adapters['http://']
        assert http_adapter.max_retries.total >= 1
        assert 429 in http_adapter.max_retries.status_forcelist

        # Now simulate the actual request flow with the mock
        # The Retry logic will call get() multiple times internally if configured correctly.
        # We mock get() to raise 429 twice then succeed.
        
        call_count = 0
        def mock_get_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                err = requests.exceptions.HTTPError("429")
                err.response = mock_response_429
                raise err
            elif call_count == 2:
                err = requests.exceptions.HTTPError("429")
                err.response = mock_response_429
                raise err
            else:
                return mock_response_200

        mock_session_instance.get.side_effect = mock_get_side_effect

        # Execute the request
        # We bypass the client.get wrapper to test the session directly with the retry logic
        # Or we test the client.get which uses the session.
        try:
            result = client.get('/data/list', timeout=5)
            # If we get here, the retry logic worked (it didn't raise on the first 429)
            assert result["datasets"][0]["name"] == "test"
            # Verify that get was called 3 times (2 failures + 1 success)
            # Note: Retry logic might behave slightly differently with mocks depending on implementation,
            # but the key is that it didn't fail on the first 429.
            assert call_count == 3
        except requests.exceptions.HTTPError:
            pytest.fail("Client failed to retry on 429")

    @patch('code.utils.api_client.requests.Session')
    def test_api_client_no_retry_on_200(self, mock_session_class):
        """
        Validates that the client does not retry on successful responses.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status.return_value = None

        mock_session_instance = MagicMock()
        mock_session_class.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock_response

        client = OpenMLClient()
        result = client.get('/test')

        assert result["status"] == "ok"
        assert mock_session_instance.get.call_count == 1

    def test_client_initialization_with_custom_backoff(self):
        """
        Validates that custom backoff factors are accepted.
        """
        client = OpenMLClient(backoff_factor=2.0, max_retries=10)
        adapter = client.session.adapters['http://']
        assert adapter.max_retries.backoff_factor == 2.0
        assert adapter.max_retries.total == 10
        assert 429 in adapter.max_retries.status_forcelist