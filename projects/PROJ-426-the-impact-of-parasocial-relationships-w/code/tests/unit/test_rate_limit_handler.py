"""
Unit tests for rate_limit_handler.py
Tests 429 response handling and integration with retry_policy.py.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.utils.rate_limit_handler import (
    RateLimitError,
    handle_429_response,
    is_rate_limited,
    extract_retry_after,
    rate_limit_handler,
    safe_api_call
)
from src.utils.retry_policy import RetryConfig

class TestRateLimitExtraction:
    """Tests for extracting Retry-After header."""

    def test_extract_retry_after_from_requests_response(self):
        """Test extraction from requests.Response object."""
        mock_response = Mock()
        mock_response.headers = {'Retry-After': '30'}
        
        result = extract_retry_after(mock_response)
        assert result == 30

    def test_extract_retry_after_from_dict(self):
        """Test extraction from dictionary response."""
        mock_response = {'Retry-After': '45'}
        
        result = extract_retry_after(mock_response)
        assert result == 45

    def test_extract_retry_after_no_header(self):
        """Test when Retry-After header is missing."""
        mock_response = Mock()
        mock_response.headers = {}
        
        result = extract_retry_after(mock_response)
        assert result is None

    def test_extract_retry_after_invalid_value(self):
        """Test handling of invalid Retry-After value."""
        mock_response = Mock()
        mock_response.headers = {'Retry-After': 'invalid'}
        
        result = extract_retry_after(mock_response)
        assert result is None

class TestIsRateLimited:
    """Tests for rate limit detection."""

    def test_is_rate_limited_requests_response(self):
        """Test detection in requests.Response."""
        mock_response = Mock()
        mock_response.status_code = 429
        
        assert is_rate_limited(mock_response) is True

    def test_is_rate_limited_dict(self):
        """Test detection in dictionary response."""
        mock_response = {'status_code': 429}
        
        assert is_rate_limited(mock_response) is True

    def test_is_not_rate_limited(self):
        """Test non-rate-limited responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        assert is_rate_limited(mock_response) is False

    def test_is_rate_limited_none(self):
        """Test None response."""
        assert is_rate_limited(None) is False

class TestHandle429Response:
    """Tests for handling 429 responses."""

    def test_handle_429_raises_after_max_retries(self):
        """Test that RateLimitError is raised after max retries."""
        mock_response = Mock()
        mock_response.headers = {}
        
        with pytest.raises(RateLimitError) as exc_info:
            handle_429_response(mock_response, attempt=5, max_retries=5)
        
        assert "rate limit exceeded" in str(exc_info.value).lower()

    def test_handle_429_respects_retry_after_header(self):
        """Test that server's Retry-After header is respected."""
        mock_response = Mock()
        mock_response.headers = {'Retry-After': '10'}
        
        # Mock time.sleep to avoid actual waiting
        with patch('src.utils.rate_limit_handler.time.sleep') as mock_sleep:
            handle_429_response(mock_response, attempt=0, max_retries=5)
            
            # Verify sleep was called with the header value
            mock_sleep.assert_called_once_with(10)

    def test_handle_429_uses_backoff_when_no_header(self):
        """Test that exponential backoff is used when no Retry-After header."""
        mock_response = Mock()
        mock_response.headers = {}
        
        with patch('src.utils.rate_limit_handler.time.sleep') as mock_sleep:
            handle_429_response(mock_response, attempt=0, max_retries=5)
            
            # Should have slept for some positive amount
            assert mock_sleep.called
            call_args = mock_sleep.call_args[0][0]
            assert call_args > 0

class TestRateLimitHandlerDecorator:
    """Tests for the rate_limit_handler decorator."""

    def test_decorator_handles_successful_response(self):
        """Test that successful responses pass through."""
        mock_func = Mock(return_value={'status_code': 200, 'data': 'success'})
        
        decorated = rate_limit_handler()(mock_func)
        result = decorated()
        
        assert result['status_code'] == 200
        assert mock_func.call_count == 1

    def test_decorator_retries_on_429(self):
        """Test that 429 responses trigger retries."""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {}
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] < 3:
                return mock_response_429
            return mock_response_200
        
        # Use a small max_retries for testing
        config = RetryConfig(max_retries=5, base_delay=0.01, max_delay=0.1)
        decorated = rate_limit_handler(retry_config=config)(mock_func)
        
        with patch('src.utils.rate_limit_handler.time.sleep'):
            result = decorated()
        
        assert result.status_code == 200
        assert call_count[0] == 3

    def test_decorator_raises_after_exhausted_retries(self):
        """Test that RateLimitError is raised after all retries exhausted."""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {}
        
        mock_func = Mock(return_value=mock_response_429)
        
        config = RetryConfig(max_retries=2, base_delay=0.01, max_delay=0.1)
        decorated = rate_limit_handler(retry_config=config)(mock_func)
        
        with patch('src.utils.rate_limit_handler.time.sleep'):
            with pytest.raises(RateLimitError):
                decorated()
        
        # Should have tried max_retries + 1 times
        assert mock_func.call_count == 3

class TestSafeApiCall:
    """Tests for safe_api_call wrapper function."""

    def test_safe_api_call_success(self):
        """Test successful API call."""
        mock_func = Mock(return_value={'status': 'ok'})
        
        result = safe_api_call(mock_func, arg1='value1')
        
        assert result['status'] == 'ok'
        mock_func.assert_called_once_with(arg1='value1')

    def test_safe_api_call_with_rate_limit(self):
        """Test API call that encounters rate limiting."""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {}
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] < 2:
                return mock_response_429
            return mock_response_200
        
        config = RetryConfig(max_retries=5, base_delay=0.01, max_delay=0.1)
        
        with patch('src.utils.rate_limit_handler.PUSHSHIFT_RETRY_CONFIG', config):
            with patch('src.utils.rate_limit_handler.time.sleep'):
                result = safe_api_call(mock_func)
        
        assert result.status_code == 200
        assert call_count[0] == 2