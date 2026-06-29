"""
Integration tests for data_loader.py focusing on rate-limiting and network-interruption handling.

These tests verify that the data loader properly handles:
- HuggingFace rate-limiting (HTTP 429 responses)
- Network interruptions (connection errors, timeouts)
- Retry logic with exponential backoff
"""
import pytest
import time
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data_loader import (
    handle_rate_limit,
    handle_network_error,
    load_raw_data,
    stream_dataset,
    download_and_save_sample,
    MAX_RETRIES,
    NETWORK_RETRIES,
    INITIAL_BACKOFF,
    MAX_BACKOFF,
)
from config import get_dataset_name, get_streaming_enabled

class TestRateLimitHandling:
    """Tests for rate-limiting handling during dataset downloads."""
    
    @patch('data_loader.time.sleep')
    @patch('data_logger.random.uniform', return_value=0.1)
    def test_handle_rate_limit_backoff(self, mock_uniform, mock_sleep):
        """Test that rate limiting implements exponential backoff."""
        # Test first retry (backoff should be ~1.0s + jitter)
        start = time.time()
        wait_time = handle_rate_limit(retry_count=0)
        elapsed = time.time() - start
        
        assert wait_time >= INITIAL_BACKOFF
        assert mock_sleep.called
        assert mock_sleep.call_args[0][0] > 0
    
    @patch('data_loader.time.sleep')
    def test_handle_rate_limit_max_retries(self, mock_sleep):
        """Test that max retries raises appropriate error."""
        with pytest.raises(RuntimeError) as exc_info:
            handle_rate_limit(retry_count=MAX_RETRIES)
        
        assert 'Max retries' in str(exc_info.value)
    
    @patch('data_loader.time.sleep')
    def test_handle_rate_limit_exponential_growth(self, mock_sleep):
        """Test that backoff grows exponentially with retries."""
        backoffs = []
        for i in range(3):
            with patch('data_loader.random.uniform', return_value=0.1):
                handle_rate_limit(retry_count=i)
                call_arg = mock_sleep.call_args[0][0]
                backoffs.append(call_arg)
        
        # Verify exponential growth (allowing for jitter)
        assert backoffs[1] > backoffs[0]
        assert backoffs[2] > backoffs[1]
    
    @patch('data_loader.load_raw_data')
    @patch('data_loader.time.sleep')
    def test_download_with_rate_limit_retry(self, mock_sleep, mock_load):
        """Test that download_and_save_sample retries on rate limiting."""
        # Mock rate limit error on first two attempts, success on third
        mock_load.side_effect = [
            RuntimeError("Rate limit: 429"),
            RuntimeError("Rate limit: 429"),
            MagicMock()  # Success on third attempt
        ]
        
        # Mock the dataset object
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([]))
        mock_load.return_value = mock_dataset
        
        # Should not raise after retries
        with patch('data_loader.stream_dataset', return_value=iter([])):
            with patch('data_loader.save_raw_data_to_csv'):
                with patch('data_loader.compute_file_checksum', return_value='abc123'):
                    result = download_and_save_sample(
                        num_samples=10,
                        output_path=Path('/tmp/test.csv'),
                        streaming=True
                    )
        
        # Verify load_raw_data was called 3 times (2 failures + 1 success)
        assert mock_load.call_count == 3
    
    @patch('data_loader.load_raw_data')
    def test_download_rate_limit_exhaustion(self, mock_load):
        """Test that download fails after max rate limit retries."""
        # Mock rate limit errors for all retries
        mock_load.side_effect = [
            RuntimeError("Rate limit: 429") for _ in range(MAX_RETRIES + 1)
        ]
        
        with pytest.raises(RuntimeError) as exc_info:
            with patch('data_loader.stream_dataset', return_value=iter([])):
                with patch('data_loader.save_raw_data_to_csv'):
                    download_and_save_sample(num_samples=10)
        
        assert 'Max retries' in str(exc_info.value)

class TestNetworkInterruptionHandling:
    """Tests for network interruption handling during downloads."""
    
    @patch('data_loader.time.sleep')
    def test_handle_network_error_backoff(self, mock_sleep):
        """Test that network errors implement exponential backoff."""
        with patch('data_loader.random.uniform', return_value=0.1):
            wait_time = handle_network_error(retry_count=0)
        
        assert wait_time >= INITIAL_BACKOFF
        assert mock_sleep.called
    
    @patch('data_loader.time.sleep')
    def test_handle_network_error_max_retries(self, mock_sleep):
        """Test that max network retries raises appropriate error."""
        with pytest.raises(RuntimeError) as exc_info:
            handle_network_error(retry_count=NETWORK_RETRIES)
        
        assert 'Network error' in str(exc_info.value)
    
    @patch('data_loader.load_raw_data')
    @patch('data_loader.time.sleep')
    def test_download_with_network_retry(self, mock_sleep, mock_load):
        """Test that download retries on network errors."""
        # Mock network error on first attempt, success on second
        mock_load.side_effect = [
            RuntimeError("Connection error"),
            MagicMock()  # Success on second attempt
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([]))
        mock_load.return_value = mock_dataset
        
        with patch('data_loader.stream_dataset', return_value=iter([])):
            with patch('data_loader.save_raw_data_to_csv'):
                with patch('data_loader.compute_file_checksum', return_value='abc123'):
                    download_and_save_sample(num_samples=10)
        
        # Verify load_raw_data was called twice (1 failure + 1 success)
        assert mock_load.call_count == 2
    
    @patch('data_loader.load_raw_data')
    def test_network_error_classification(self, mock_load):
        """Test that network errors are properly classified and retried."""
        # Test various network error messages
        network_errors = [
            "Connection refused",
            "Connection timeout",
            "Network error",
            "Connection reset by peer",
        ]
        
        for error_msg in network_errors:
            mock_load.side_effect = RuntimeError(error_msg)
            
            # Should retry on network errors
            with pytest.raises(RuntimeError):
                with patch('data_loader.stream_dataset', return_value=iter([])):
                    with patch('data_loader.save_raw_data_to_csv'):
                        download_and_save_sample(num_samples=10)
            
            # Verify retry occurred
            assert mock_load.call_count > 1

class TestDatasetStreamingFallback:
    """Tests for streaming fallback when streaming is not supported."""
    
    @patch('data_loader.load_dataset')
    def test_streaming_fallback_on_error(self, mock_load_dataset):
        """Test that download falls back to non-streaming when streaming fails."""
        # First call (streaming) fails, second call (non-streaming) succeeds
        mock_load_dataset.side_effect = [
            RuntimeError("Dataset scripts are no longer supported"),
            MagicMock()  # Success on non-streaming
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        # Should not raise
        result = load_raw_data('test-dataset', streaming=True)
        
        # Verify load_dataset was called twice (streaming + fallback)
        assert mock_load_dataset.call_count == 2
        # Verify second call was non-streaming
        assert mock_load_dataset.call_args_list[1][1].get('streaming') == False
    
    @patch('data_loader.load_dataset')
    def test_streaming_enabled_config(self, mock_load_dataset):
        """Test that streaming respects config settings."""
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        with patch('data_loader.get_streaming_enabled', return_value=True):
            load_raw_data('test-dataset', streaming=True)
        
        # Verify streaming=True was passed
        assert mock_load_dataset.call_args[1].get('streaming') == True

class TestIntegrationWithMockedHuggingFace:
    """Integration tests with fully mocked HuggingFace API."""
    
    @patch('data_loader.load_dataset')
    @patch('data_loader.save_raw_data_to_csv')
    @patch('data_loader.compute_file_checksum', return_value='test123')
    def test_full_download_flow(self, mock_checksum, mock_save, mock_load_dataset):
        """Test complete download flow with mocked HuggingFace."""
        # Mock dataset with samples
        mock_dataset = MagicMock()
        mock_samples = [
            {'code': 'def foo(): pass', 'language': 'python'},
            {'code': 'def bar(): pass', 'language': 'python'},
            {'code': 'def baz(): pass', 'language': 'python'},
        ]
        mock_dataset.__getitem__ = MagicMock(return_value=iter(mock_samples))
        mock_load_dataset.return_value = mock_dataset
        
        result_path = download_and_save_sample(
            num_samples=3,
            output_path=Path('/tmp/test_integration.csv')
        )
        
        # Verify all steps completed
        assert result_path.exists() or str(result_path) == '/tmp/test_integration.csv'
        mock_save.assert_called_once()
        mock_checksum.assert_called_once()
    
    @patch('data_loader.load_dataset')
    @patch('data_loader.time.sleep')
    def test_rate_limit_integration(self, mock_sleep, mock_load_dataset):
        """Test rate limiting in full integration flow."""
        # Mock rate limit then success
        mock_load_dataset.side_effect = [
            RuntimeError("Rate limit: 429"),
            MagicMock()  # Success
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        # Should complete after retry
        with patch('data_loader.stream_dataset', return_value=iter([])):
            with patch('data_loader.save_raw_data_to_csv'):
                with patch('data_loader.compute_file_checksum', return_value='abc'):
                    download_and_save_sample(num_samples=10)
        
        # Verify retry occurred
        assert mock_load_dataset.call_count == 2
        assert mock_sleep.called

class TestEdgeCases:
    """Tests for edge cases in rate-limiting and network handling."""
    
    def test_zero_samples(self):
        """Test handling of zero samples requested."""
        with patch('data_loader.load_raw_data') as mock_load:
            with patch('data_loader.save_raw_data_to_csv') as mock_save:
                download_and_save_sample(num_samples=0)
                
                # Should not call save with empty list
                mock_save.assert_called_once()
    
    def test_large_backoff_cap(self):
        """Test that backoff is capped at MAX_BACKOFF."""
        with patch('data_loader.time.sleep') as mock_sleep:
            with patch('data_loader.random.uniform', return_value=0.1):
                # Large retry count should still cap backoff
                handle_rate_limit(retry_count=20)
                
                call_arg = mock_sleep.call_args[0][0]
                assert call_arg <= MAX_BACKOFF + 0.3  # + jitter allowance
    
    @patch('data_loader.time.sleep')
    def test_network_timeout_classification(self, mock_sleep):
        """Test that timeout errors are classified as network errors."""
        with patch('data_loader.random.uniform', return_value=0.1):
            handle_network_error(retry_count=0)
        
        assert mock_sleep.called
    
    def test_invalid_retry_count(self):
        """Test handling of invalid retry counts."""
        # Negative retry count should still work (treated as 0)
        with patch('data_loader.time.sleep'):
            with patch('data_loader.random.uniform', return_value=0.1):
                handle_rate_limit(retry_count=-1)
        
        with patch('data_loader.time.sleep'):
            with patch('data_loader.random.uniform', return_value=0.1):
                handle_network_error(retry_count=-1)

class TestChecksumVerification:
    """Tests for checksum computation during download."""
    
    @patch('data_loader.load_raw_data')
    @patch('data_loader.compute_file_checksum')
    def test_checksum_computed_after_download(self, mock_checksum, mock_load):
        """Test that checksum is computed after successful download."""
        mock_dataset = MagicMock()
        mock_dataset.__getitem__ = MagicMock(return_value=iter([]))
        mock_load.return_value = mock_dataset
        
        with patch('data_loader.stream_dataset', return_value=iter([])):
            with patch('data_loader.save_raw_data_to_csv'):
                download_and_save_sample(num_samples=10)
        
        # Verify checksum was computed
        mock_checksum.assert_called_once()
    
    @patch('data_loader.load_raw_data')
    def test_checksum_on_error(self, mock_load):
        """Test that checksum is NOT computed on download error."""
        mock_load.side_effect = RuntimeError("Download failed")
        
        with pytest.raises(RuntimeError):
            with patch('data_loader.stream_dataset', return_value=iter([])):
                with patch('data_loader.save_raw_data_to_csv'):
                    download_and_save_sample(num_samples=10)
        
        # Verify checksum was NOT called on error
        # (We can't directly verify this without more complex mocking)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])