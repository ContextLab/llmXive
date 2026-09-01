"""
Unit tests for API retry logic and timeout handling in the LLM client.

Tests cover:
- Retry logic on transient failures (rate limits, server errors)
- Timeout handling (request exceeds configured limit)
- Exponential backoff behavior
- Max attempts limit enforcement
"""
import pytest
import time
from unittest.mock import patch, MagicMock, Mock
from requests.exceptions import Timeout, HTTPError, RequestException
from typing import List, Dict, Any
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import Config
from utils.logging import LLMRefactoringError, get_logger
from llm.refactoring import LLMClient


class TestLLMClientRetryLogic:
    """Tests for retry logic and timeout handling in LLMClient."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config with test values."""
        config = MagicMock(spec=Config)
        config.HF_API_KEY = "test-key"
        config.MAX_ATTEMPTS = 3
        config.RANDOM_SEED = 42
        config.MIN_VALID_FUNCTIONS = 100
        config.BATCH_SIZE = 10
        return config

    @pytest.fixture
    def client(self, mock_config):
        """Create an LLMClient instance with mocked config."""
        return LLMClient(config=mock_config)

    def test_retry_on_rate_limit(self, client):
        """Test that the client retries on 429 (rate limit) errors."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        # Mock the session to raise 429 twice, then succeed
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                mock_response = MagicMock()
                mock_response.status_code = 429
                mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
                mock_response.raise_for_status()
            else:
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.json.return_value = {"generated_text": "refactored code"}
                return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            result = client._make_request("test prompt", timeout=60, max_attempts=3)
            assert result is not None
            assert result["generated_text"] == "refactored code"
            assert call_count == 3  # 2 failures + 1 success

    def test_retry_on_server_error(self, client):
        """Test that the client retries on 500 (server error) errors."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
                mock_response.raise_for_status()
            else:
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.json.return_value = {"generated_text": "success"}
                return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            result = client._make_request("test prompt", timeout=60, max_attempts=3)
            assert result is not None
            assert call_count == 2

    def test_timeout_handling(self, client):
        """Test that timeout exceptions are raised correctly."""
        with patch.object(client.session, 'post', side_effect=Timeout("Request timed out")):
            with pytest.raises(LLMRefactoringError) as exc_info:
                client._make_request("test prompt", timeout=60, max_attempts=1)
            
            assert "timeout" in str(exc_info.value).lower()

    def test_max_attempts_exceeded(self, client):
        """Test that the client stops after max_attempts and raises an error."""
        def side_effect(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
            mock_response.raise_for_status()

        with patch.object(client.session, 'post', side_effect=side_effect):
            with pytest.raises(LLMRefactoringError) as exc_info:
                client._make_request("test prompt", timeout=60, max_attempts=3)
            
            assert "max attempts" in str(exc_info.value).lower()
            assert "exceeded" in str(exc_info.value).lower()

    def test_exponential_backoff_timing(self, client):
        """Test that exponential backoff is applied between retries."""
        call_times = []
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                mock_response = MagicMock()
                mock_response.status_code = 429
                mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
                mock_response.raise_for_status()
            else:
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.json.return_value = {"generated_text": "success"}
                return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            # Use very short backoff for testing (base=0.1s)
            with patch.object(client, '_get_backoff', return_value=0.1):
                result = client._make_request("test prompt", timeout=60, max_attempts=3)
                assert result is not None

        # Verify that there was a delay between calls
        if len(call_times) >= 2:
            # The delay should be at least the backoff time (with some tolerance)
            delay = call_times[1] - call_times[0]
            assert delay >= 0.05  # At least 50ms delay (allowing for timing variance)

    def test_no_retry_on_client_error(self, client):
        """Test that 4xx errors (except 429) are not retried."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        with patch.object(client.session, 'post', side_effect=mock_response.raise_for_status):
            with pytest.raises(LLMRefactoringError) as exc_info:
                client._make_request("test prompt", timeout=60, max_attempts=3)
            
            assert "client error" in str(exc_info.value).lower()

    def test_successful_request_no_retry(self, client):
        """Test that successful requests don't trigger retries."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"generated_text": "success"}

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            result = client._make_request("test prompt", timeout=60, max_attempts=3)
            assert result is not None
            assert call_count == 1  # Only one call, no retries

    def test_network_error_retry(self, client):
        """Test that network errors (RequestException) are retried."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RequestException("Network error")
            else:
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.json.return_value = {"generated_text": "success"}
                return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            result = client._make_request("test prompt", timeout=60, max_attempts=3)
            assert result is not None
            assert call_count == 2

    def test_timeout_parameter_passed(self, client):
        """Test that the timeout parameter is correctly passed to the request."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"generated_text": "success"}

        captured_timeout = None
        def side_effect(*args, **kwargs):
            nonlocal captured_timeout
            captured_timeout = kwargs.get('timeout')
            return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            client._make_request("test prompt", timeout=120, max_attempts=1)
            assert captured_timeout == 120

    def test_retry_logic_with_config_max_attempts(self, client, mock_config):
        """Test that the client uses the configured MAX_ATTEMPTS value."""
        mock_config.MAX_ATTEMPTS = 5
        client = LLMClient(config=mock_config)
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
                mock_response.raise_for_status()
            else:
                success_response = MagicMock()
                success_response.status_code = 200
                success_response.json.return_value = {"generated_text": "success"}
                return success_response

        with patch.object(client.session, 'post', side_effect=side_effect):
            # Should use config's MAX_ATTEMPTS (5) when not explicitly passed
            result = client._make_request("test prompt", timeout=60)
            assert result is not None
            assert call_count == 5