import pytest
import time
from unittest.mock import patch, MagicMock, Mock
from code.utils.network import exponential_backoff_request, MaxRetriesError, fetch_file_with_retry
from urllib.error import URLError, HTTPError

class TestRetryExponentialBackoff:
    def test_success_on_first_attempt(self):
        """Test that a successful request returns immediately."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"test data"

        with patch('code.utils.network.urlopen', return_value=mock_response) as mock_urlopen:
            result = exponential_backoff_request("http://example.com/file.txt")
            assert result is mock_response
            mock_urlopen.assert_called_once()

    def test_retry_on_transient_error(self):
        """Test that the function retries on URLError before succeeding."""
        mock_response = MagicMock()
        
        # First two calls fail, third succeeds
        mock_urlopen = MagicMock()
        mock_urlopen.side_effect = [
            URLError("Network error"),
            URLError("Network error"),
            mock_response
        ]

        with patch('code.utils.network.urlopen', mock_urlopen):
            # We patch time.sleep to avoid actual waiting in tests
            with patch('code.utils.network.time.sleep'):
                result = exponential_backoff_request("http://example.com/file.txt")
                assert result is mock_response
                assert mock_urlopen.call_count == 3

    def test_max_retries_exceeded_raises_error(self):
        """Test that MaxRetriesError is raised after max_retries attempts."""
        max_retries = 3
        
        mock_urlopen = MagicMock()
        mock_urlopen.side_effect = URLError("Persistent network error")

        with patch('code.utils.network.urlopen', mock_urlopen):
            with patch('code.utils.network.time.sleep'):
                with pytest.raises(MaxRetriesError) as exc_info:
                    exponential_backoff_request(
                        "http://example.com/file.txt",
                        max_retries=max_retries
                    )
                
                assert f"Failed to fetch http://example.com/file.txt after {max_retries} retries" in str(exc_info.value)
                # Should attempt initial + retries
                assert mock_urlopen.call_count == max_retries + 1

    def test_exponential_backoff_delays(self):
        """Test that delays increase exponentially between retries."""
        mock_urlopen = MagicMock()
        mock_urlopen.side_effect = URLError("Network error")
        
        delays = []
        original_sleep = time.sleep
        
        def capture_sleep(delay):
            delays.append(delay)
            # Don't actually sleep, just record the delay

        with patch('code.utils.network.urlopen', mock_urlopen):
            with patch('code.utils.network.time.sleep', side_effect=capture_sleep):
                with pytest.raises(MaxRetriesError):
                    exponential_backoff_request(
                        "http://example.com/file.txt",
                        max_retries=3,
                        initial_delay=1.0,
                        max_delay=10.0
                    )

        # Verify exponential growth (with jitter, exact values vary, but trend should be increasing)
        assert len(delays) == 3  # 3 retries
        # Check that delays are generally increasing (allowing for small jitter)
        for i in range(1, len(delays)):
            # Delay should be roughly double the previous, minus small jitter
            assert delays[i] >= delays[i-1] * 0.9  # Allow for jitter

    def test_fetch_file_with_retry_writes_to_disk(self, tmp_path):
        """Test that fetch_file_with_retry actually writes the file to disk."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"binary file content"
        
        dest_file = tmp_path / "test_file.txt"

        with patch('code.utils.network.urlopen', return_value=mock_response):
            result_path = fetch_file_with_retry("http://example.com/file.txt", str(dest_file))

        assert result_path == dest_file
        assert dest_file.exists()
        assert dest_file.read_bytes() == b"binary file content"

    def test_fetch_file_creates_parent_directories(self, tmp_path):
        """Test that fetch_file_with_retry creates parent directories if they don't exist."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"data"
        
        nested_path = tmp_path / "subdir" / "nested" / "file.txt"

        with patch('code.utils.network.urlopen', return_value=mock_response):
            fetch_file_with_retry("http://example.com/file.txt", str(nested_path))

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_http_5xx_error_triggers_retry(self):
        """Test that HTTP 5xx errors trigger retry logic."""
        mock_response = MagicMock()
        
        # First two calls return 503, third succeeds
        mock_urlopen = MagicMock()
        mock_urlopen.side_effect = [
            HTTPError("http://example.com", 503, "Service Unavailable", {}, None),
            HTTPError("http://example.com", 503, "Service Unavailable", {}, None),
            mock_response
        ]

        with patch('code.utils.network.urlopen', mock_urlopen):
            with patch('code.utils.network.time.sleep'):
                result = exponential_backoff_request("http://example.com/file.txt")
                assert result is mock_response
                assert mock_urlopen.call_count == 3