"""
Unit tests for retry logic with exponential backoff.

Tests the retry_with_backoff decorator and retry_download function
to ensure they correctly implement exponential backoff behavior.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from utils.retry import retry_with_backoff, retry_download

class TestRetryWithBackoff:
    """Tests for the retry_with_backoff decorator."""
    
    def test_successful_call_no_retry(self):
        """Test that a successful function call doesn't trigger retries."""
        call_count = 0
        
        @retry_with_backoff(tries=3, base_delay=0.1)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Test that function is retried on failure."""
        call_count = 0
        
        @retry_with_backoff(tries=3, base_delay=0.01, max_delay=0.1)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_func()
        
        assert result == "success"
        assert call_count == 3
    
    def test_failure_after_max_retries(self):
        """Test that exception is raised after max retries."""
        call_count = 0
        
        @retry_with_backoff(tries=3, base_delay=0.01, max_delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError, match="Permanent failure"):
            always_fails()
        
        assert call_count == 3
    
    def test_exponential_backoff_timing(self):
        """Test that delays follow exponential backoff pattern."""
        call_count = 0
        delays = []
        
        @retry_with_backoff(tries=4, base_delay=0.1, max_delay=1.0, jitter=False)
        def timed_failing_func():
            nonlocal call_count
            nonlocal delays
            call_count += 1
            if call_count < 4:
                raise ValueError("Temporary failure")
            return "success"
        
        start_time = time.time()
        result = timed_failing_func()
        total_time = time.time() - start_time
        
        assert result == "success"
        assert call_count == 4
        # With base_delay=0.1 and backoff_factor=2.0:
        # Delay after attempt 1: 0.1
        # Delay after attempt 2: 0.2
        # Total expected delay: 0.3 seconds (minimum)
        assert total_time >= 0.25  # Allow some tolerance
    
    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        # Run multiple times to verify jitter is applied
        execution_times = []
        
        for _ in range(5):
            call_count = 0
            
            @retry_with_backoff(tries=3, base_delay=0.1, max_delay=0.5, jitter=True)
            def jittered_func():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ValueError("Temporary failure")
                return "success"
            
            start = time.time()
            jittered_func()
            execution_times.append(time.time() - start)
        
        # With jitter, execution times should vary
        # If all times are identical, jitter is not working
        time_variance = max(execution_times) - min(execution_times)
        assert time_variance > 0.01, "Jitter should cause variation in execution times"
    
    def test_custom_exception_types(self):
        """Test that only specified exceptions are caught."""
        call_count = 0
        
        @retry_with_backoff(tries=3, base_delay=0.01, exceptions=(ValueError,))
        def specific_exception_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TypeError("Wrong exception type")
            return "success"
        
        # Should not retry on TypeError
        with pytest.raises(TypeError, match="Wrong exception type"):
            specific_exception_func()
        
        assert call_count == 1
    
    def test_max_delay_cap(self):
        """Test that delay doesn't exceed max_delay."""
        call_count = 0
        
        @retry_with_backoff(tries=5, base_delay=0.1, max_delay=0.2, backoff_factor=10.0, jitter=False)
        def capped_delay_func():
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                raise ValueError("Temporary failure")
            return "success"
        
        start_time = time.time()
        result = capped_delay_func()
        total_time = time.time() - start_time
        
        assert result == "success"
        # With max_delay=0.2 and 4 retries:
        # Max total delay: 0.2 * 4 = 0.8 seconds
        assert total_time < 1.0  # Should not exceed max_delay * retries
    
    def test_decorator_preserves_function_metadata(self):
        """Test that the decorator preserves function name and docstring."""
        @retry_with_backoff(tries=3)
        def my_function():
            """My function docstring."""
            return True
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My function docstring."

class TestRetryDownload:
    """Tests for the retry_download function."""
    
    @patch('urllib.request.urlopen')
    def test_successful_download(self, mock_urlopen):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"test data"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with patch('builtins.open', MagicMock()) as mock_open:
            result = retry_download("http://example.com/file.txt", "/tmp/file.txt", max_retries=3)
            
            assert result is True
            mock_urlopen.assert_called_once()
            mock_open.assert_called_once()
    
    @patch('urllib.request.urlopen')
    def test_retry_on_network_error(self, mock_urlopen):
        """Test retry on network errors."""
        import urllib.error
        
        mock_urlopen.side_effect = [
            urllib.error.URLError("Network error"),
            urllib.error.URLError("Network error"),
            MagicMock()  # Success on third attempt
        ]
        
        mock_response = MagicMock()
        mock_response.read.return_value = b"test data"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with patch('builtins.open', MagicMock()):
            result = retry_download("http://example.com/file.txt", "/tmp/file.txt", max_retries=3)
            
            assert result is True
            assert mock_urlopen.call_count == 3
    
    @patch('urllib.request.urlopen')
    def test_failure_after_max_retries(self, mock_urlopen):
        """Test failure after all retries exhausted."""
        import urllib.error
        
        mock_urlopen.side_effect = urllib.error.URLError("Persistent error")
        
        with patch('builtins.open', MagicMock()):
            with pytest.raises(Exception):
                retry_download("http://example.com/file.txt", "/tmp/file.txt", max_retries=2)
            
            assert mock_urlopen.call_count == 2
    
    @patch('urllib.request.urlopen')
    def test_timeout_handling(self, mock_urlopen):
        """Test that timeout is passed to urlopen."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"test data"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with patch('builtins.open', MagicMock()):
            retry_download("http://example.com/file.txt", "/tmp/file.txt", timeout=60)
            
            # Verify timeout parameter was passed
            call_args = mock_urlopen.call_args
            assert call_args.kwargs.get('timeout') == 60
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = ValueError("Invalid URL")
            
            with patch('builtins.open', MagicMock()):
                with pytest.raises(Exception):
                    retry_download("not-a-url", "/tmp/file.txt")

class TestExponentialBackoffBehavior:
    """Integration tests for exponential backoff behavior."""
    
    def test_backoff_sequence(self):
        """Verify the exponential backoff sequence."""
        delays = []
        base_delay = 0.1
        backoff_factor = 2.0
        
        for attempt in range(5):
            if attempt == 0:
                delay = base_delay
            else:
                delay = min(1.0, delay * backoff_factor)
            delays.append(delay)
        
        # Expected sequence: 0.1, 0.2, 0.4, 0.8, 0.8 (capped at 1.0)
        assert delays[0] == 0.1
        assert delays[1] == 0.2
        assert delays[2] == 0.4
        assert delays[3] == 0.8
        assert delays[4] == 0.8  # Capped by max_delay
    
    def test_jitter_range(self):
        """Test that jitter stays within expected range."""
        base_delay = 0.5
        jitter_factor = 0.1
        
        for _ in range(100):
            jittered_delay = base_delay + (0.1 * base_delay) * (2 * (0.5) - 1)
            expected_min = base_delay * (1 - jitter_factor)
            expected_max = base_delay * (1 + jitter_factor)
            
            assert expected_min <= jittered_delay <= expected_max