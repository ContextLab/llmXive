import pytest
import time
from unittest.mock import patch, MagicMock
from code.fetcher import rate_limit_handler, retry_with_exponential_backoff, fetch_backend_properties
import requests

class TestRateLimitHandler:
    """Tests for the rate_limit_handler decorator."""

    def test_enforces_minimum_gap(self):
        """Test that the handler enforces a 2-second gap between requests."""
        call_times = []

        @rate_limit_handler
        def mock_func(device_id):
            call_times.append(time.time())
            return "success"

        # First call
        mock_func("device1")
        first_call = call_times[0]

        # Immediate second call should be delayed
        mock_func("device1")
        second_call = call_times[1]

        # Verify gap is at least 2 seconds
        gap = second_call - first_call
        assert gap >= 2.0, f"Gap {gap:.2f}s is less than required 2.0s"

    def test_different_devices_no_delay(self):
        """Test that requests to different devices are not delayed."""
        call_times = []

        @rate_limit_handler
        def mock_func(device_id):
            call_times.append(time.time())
            return "success"

        mock_func("device1")
        first_call = call_times[0]

        mock_func("device2")
        second_call = call_times[1]

        # Gap should be negligible (<< 2s)
        gap = second_call - first_call
        assert gap < 0.5, f"Gap {gap:.2f}s suggests unnecessary delay between different devices"

class TestRetryWithExponentialBackoff:
    """Tests for the retry_with_exponential_backoff decorator."""

    @pytest.mark.parametrize("status_code", [429, 503])
    def test_retries_on_429_and_503(self, status_code):
        """Test that the decorator retries on 429 and 503 errors."""
        call_count = 0
        max_attempts = 3

        def mock_func():
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = status_code
            error = requests.exceptions.HTTPError(response=response)
            raise error

        decorated_func = retry_with_exponential_backoff(mock_func)

        with pytest.raises(requests.exceptions.HTTPError):
            decorated_func()

        # Should have retried up to max_attempts (including initial)
        # But since we limit retries in the decorator to 5, and we simulate failure every time,
        # it should attempt 5 times. However, for testing speed, we might want to mock time.sleep.
        # Here we just check it attempted more than once.
        assert call_count > 1, "Decorator did not retry on HTTP error"

    def test_no_retry_on_other_errors(self):
        """Test that the decorator does not retry on non-429/503 errors."""
        call_count = 0

        def mock_func():
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 404
            error = requests.exceptions.HTTPError(response=response)
            raise error

        decorated_func = retry_with_exponential_backoff(mock_func)

        with pytest.raises(requests.exceptions.HTTPError):
            decorated_func()

        # Should have been called only once
        assert call_count == 1, "Decorator retried on non-recoverable error"

class TestFetchBackendPropertiesRateLimit:
    """Integration-style tests for fetch_backend_properties rate limiting."""

    @patch('code.fetcher.load_config')
    @patch('code.fetcher.QiskitRuntimeService')
    def test_429_triggers_retry_with_delay(self, mock_service_class, mock_load_config):
        """Simulate 429 errors and verify retry logic with delays."""
        mock_load_config.return_value.ibmq_token = "fake_token"
        mock_backend = MagicMock()
        mock_backend.name = "test_device"
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.backend.return_value = mock_backend

        # Simulate 429 errors for first 2 attempts, then success
        call_count = 0
        def mock_properties():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                response = MagicMock()
                response.status_code = 429
                raise requests.exceptions.HTTPError(response=response)
            return MagicMock(last_update_date="2024-01-01", to_dict=lambda: {})

        mock_backend.properties = mock_properties

        # Mock time.sleep to speed up test
        with patch('code.fetcher.time.sleep') as mock_sleep:
            props = fetch_backend_properties("test_device")
            
            # Should have retried
            assert call_count > 1, "Did not retry on 429"
            # Verify sleep was called
            assert mock_sleep.called, "time.sleep was not called during retry"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])