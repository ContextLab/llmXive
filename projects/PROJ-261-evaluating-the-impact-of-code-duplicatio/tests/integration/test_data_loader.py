"""
Integration test for HuggingFace rate-limiting and network-interruption handling
during 500 MB download (T015a - US1)

This test validates that the data_loader.py correctly handles:
1. Rate-limiting (HTTP 429) from HuggingFace Hub
2. Network interruptions during download
3. Retry logic with exponential backoff

Per spec.md Independent Test requirements for US1.
"""

import pytest
import time
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
from requests.exceptions import ConnectionError, Timeout
from http.client import RemoteDisconnected

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplicatio' / 'code'))

from data_loader import (
    setup_logging,
    handle_rate_limit,
    handle_network_error,
    stream_dataset,
    save_raw_data_to_csv,
    download_and_save_sample
)
from config import (
    get_dataset_name,
    get_streaming_enabled,
    get_random_seed
)

# Test constants
TEST_OUTPUT_DIR = Path(project_root / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplicatio' / 'data' / 'raw')
TEST_OUTPUT_FILE = TEST_OUTPUT_DIR / 'github-code-sample.csv'
TEST_MAX_SAMPLES = 10
TEST_RETRY_COUNT = 3
TEST_BACKOFF_FACTOR = 0.5

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Setup test environment before each test."""
    # Ensure output directory exists
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after test (optional - keep for debugging)
    # if TEST_OUTPUT_FILE.exists():
    #     TEST_OUTPUT_FILE.unlink()

class TestRateLimitingHandling:
    """Test rate-limiting (HTTP 429) handling during download."""
    
    def test_handle_rate_limit_with_retry(self):
        """
        Test that handle_rate_limit correctly handles 429 responses
        with exponential backoff and retry logic.
        """
        retry_count = 0
        max_retries = 3
        
        def mock_rate_limit_func():
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_retries:
                raise Exception("Rate limit exceeded (429)")
            return {"success": True, "data": "sample"}
        
        result = handle_rate_limit(mock_rate_limit_func, max_retries=max_retries, backoff_factor=0.01)
        
        assert result is not None
        assert result.get("success") is True
        assert retry_count == max_retries
    
    def test_handle_rate_limit_exceeds_max_retries(self):
        """
        Test that handle_rate_limit raises exception after max retries exceeded.
        """
        def always_fail():
            raise Exception("Rate limit exceeded (429)")
        
        with pytest.raises(Exception) as exc_info:
            handle_rate_limit(always_fail, max_retries=2, backoff_factor=0.01)
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @patch('datasets.load_dataset')
    def test_stream_dataset_rate_limit_retry(self, mock_load_dataset):
        """
        Test that stream_dataset handles rate limits during HuggingFace dataset loading.
        """
        # Setup mock to fail twice then succeed
        call_count = [0]
        
        def mock_load_with_retry(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                # Simulate rate limit response
                mock_dataset = MagicMock()
                mock_dataset.__iter__ = MagicMock(side_effect=Exception("Rate limit (429)"))
                return mock_dataset
            
            # Success on third attempt
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = MagicMock(return_value=[
                {"code": "print('hello')", "path": "test.py"},
                {"code": "def foo(): pass", "path": "test2.py"}
            ])
            return mock_dataset
        
        mock_load_dataset.side_effect = mock_load_with_retry
        
        # This should retry and eventually succeed
        dataset = stream_dataset(
            dataset_name="codeparrot/github-code",
            split="train",
            streaming=True,
            max_samples=TEST_MAX_SAMPLES,
            max_retries=3
        )
        
        assert dataset is not None
        assert call_count[0] >= 3  # Should have retried at least twice
    
    def test_rate_limit_with_exponential_backoff(self):
        """
        Test that rate limit handling uses exponential backoff timing.
        """
        retry_timestamps = []
        
        def mock_func():
            nonlocal retry_timestamps
            retry_timestamps.append(time.time())
            if len(retry_timestamps) < 3:
                raise Exception("429 Rate Limit")
            return {"data": "success"}
        
        result = handle_rate_limit(
            mock_func,
            max_retries=3,
            backoff_factor=0.1
        )
        
        assert result is not None
        assert len(retry_timestamps) == 3
        
        # Check that delays between retries increase (exponential backoff)
        if len(retry_timestamps) >= 2:
            first_delay = retry_timestamps[1] - retry_timestamps[0]
            second_delay = retry_timestamps[2] - retry_timestamps[1]
            
            # Second delay should be >= first delay (exponential backoff)
            assert second_delay >= first_delay - 0.05  # Allow small timing variance

class TestNetworkInterruptionHandling:
    """Test network interruption handling during download."""
    
    def test_handle_network_error_with_retry(self):
        """
        Test that handle_network_error correctly handles connection errors
        with retry logic.
        """
        retry_count = 0
        max_retries = 3
        
        def mock_network_func():
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_retries:
                raise ConnectionError("Network interrupted")
            return {"success": True, "data": "recovered"}
        
        result = handle_network_error(mock_network_func, max_retries=max_retries)
        
        assert result is not None
        assert result.get("success") is True
        assert retry_count == max_retries
    
    def test_handle_network_error_various_exception_types(self):
        """
        Test that handle_network_error handles various network-related exceptions.
        """
        exception_types = [
            ConnectionError("Connection lost"),
            Timeout("Request timed out"),
            RemoteDisconnected("Remote end closed connection"),
            OSError("Network unreachable")
        ]
        
        for exc_type in exception_types:
            call_count = [0]
            
            def mock_func():
                call_count[0] += 1
                if call_count[0] < 2:
                    raise exc_type
                return {"recovered": True}
            
            result = handle_network_error(mock_func, max_retries=2)
            assert result is not None
            assert result.get("recovered") is True
    
    @patch('datasets.load_dataset')
    def test_stream_dataset_network_interruption(self, mock_load_dataset):
        """
        Test that stream_dataset handles network interruptions during HuggingFace download.
        """
        call_count = [0]
        
        def mock_load_with_network_fail(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                # Simulate network interruption
                raise ConnectionError("Network interrupted during download")
            
            # Success on second attempt
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = MagicMock(return_value=[
                {"code": "x = 1", "path": "a.py"},
                {"code": "y = 2", "path": "b.py"}
            ])
            return mock_dataset
        
        mock_load_dataset.side_effect = mock_load_with_network_fail
        
        dataset = stream_dataset(
            dataset_name="codeparrot/github-code",
            split="train",
            streaming=True,
            max_samples=TEST_MAX_SAMPLES,
            max_retries=2
        )
        
        assert dataset is not None
        assert call_count[0] >= 2  # Should have retried
    
    def test_network_error_with_connection_reset(self):
        """
        Test handling of ConnectionResetError during download.
        """
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionResetError("Connection reset by peer")
            return {"success": True}
        
        result = handle_network_error(mock_func, max_retries=2)
        assert result is not None
        assert result.get("success") is True

class TestDownloadIntegration:
    """Integration tests for the complete download workflow."""
    
    @patch('datasets.load_dataset')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_download_and_save_sample_with_rate_limit_retry(self, mock_mkdir, mock_exists, mock_load_dataset):
        """
        Integration test: download_and_save_sample handles rate limits
        and produces the expected output file.
        """
        mock_exists.return_value = False  # Directory doesn't exist initially
        
        # Setup mock to simulate rate limit then success
        call_count = [0]
        
        def mock_load_with_retry(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Rate limit (429)")
            
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = MagicMock(return_value=[
                {"code": "def hello():\n    print('world')", "path": "hello.py"},
                {"code": "class Foo:\n    pass", "path": "foo.py"}
            ])
            return mock_dataset
        
        mock_load_dataset.side_effect = mock_load_with_retry
        
        output_path = TEST_OUTPUT_DIR / 'test_sample.csv'
        
        result = download_and_save_sample(
            output_path=output_path,
            max_samples=2,
            dataset_name="codeparrot/github-code",
            max_retries=2
        )
        
        assert result is True
        assert call_count[0] >= 2  # Should have retried
    
    @patch('datasets.load_dataset')
    def test_stream_dataset_produces_correct_data_format(self, mock_load_dataset):
        """
        Test that stream_dataset produces data in the expected format.
        """
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=[
            {"code": "print('test')", "path": "test.py", "language": "python"},
            {"code": "def foo(): pass", "path": "foo.py", "language": "python"}
        ])
        mock_load_dataset.return_value = mock_dataset
        
        dataset = stream_dataset(
            dataset_name="codeparrot/github-code",
            split="train",
            streaming=True,
            max_samples=TEST_MAX_SAMPLES
        )
        
        assert dataset is not None
        
        # Verify we can iterate and get expected fields
        items = list(dataset)
        assert len(items) == 2
        assert all("code" in item for item in items)
        assert all("path" in item for item in items)
    
    @patch('datasets.load_dataset')
    def test_download_handles_empty_dataset(self, mock_load_dataset):
        """
        Test that download handles empty dataset gracefully.
        """
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=[])
        mock_load_dataset.return_value = mock_dataset
        
        dataset = stream_dataset(
            dataset_name="codeparrot/github-code",
            split="train",
            streaming=True,
            max_samples=TEST_MAX_SAMPLES
        )
        
        assert dataset is not None
        items = list(dataset)
        assert len(items) == 0

class TestErrorRecoveryScenarios:
    """Test various error recovery scenarios during download."""
    
    def test_multiple_consecutive_rate_limits(self):
        """
        Test recovery from multiple consecutive rate limit errors.
        """
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] < 4:
                raise Exception("Rate limit (429)")
            return {"data": "success after 3 retries"}
        
        result = handle_rate_limit(mock_func, max_retries=4, backoff_factor=0.01)
        
        assert result is not None
        assert result.get("data") == "success after 3 retries"
        assert call_count[0] == 4
    
    def test_network_error_then_rate_limit_then_success(self):
        """
        Test recovery from mixed error types (network error, then rate limit, then success).
        """
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Network error")
            elif call_count[0] == 2:
                raise Exception("Rate limit (429)")
            return {"recovered": True, "errors_handled": 2}
        
        # First try network error handler
        result = handle_network_error(mock_func, max_retries=3)
        assert result is not None
        assert result.get("recovered") is True

class TestLoggingAndMonitoring:
    """Test that errors are properly logged during download."""
    
    def test_rate_limit_logging(self):
        """
        Test that rate limit errors are logged appropriately.
        """
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Rate limit (429)")
            return {"success": True}
        
        # Capture logger output
        with patch('logging.Logger.warning') as mock_warning:
            result = handle_rate_limit(mock_func, max_retries=2)
            
            assert result is not None
            assert mock_warning.called  # Should have logged retry attempts
    
    def test_network_error_logging(self):
        """
        Test that network errors are logged appropriately.
        """
        call_count = [0]
        
        def mock_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Network interrupted")
            return {"success": True}
        
        with patch('logging.Logger.warning') as mock_warning:
            result = handle_network_error(mock_func, max_retries=2)
            
            assert result is not None
            assert mock_warning.called

class Test500MBDownloadSimulation:
    """Test scenarios simulating 500 MB download with interruptions."""
    
    def test_large_download_with_interruption_recovery(self):
        """
        Simulate a 500 MB download that gets interrupted and recovers.
        """
        bytes_downloaded = [0]
        target_bytes = 500 * 1024 * 1024  # 500 MB
        chunk_size = 10 * 1024 * 1024  # 10 MB chunks
        
        def mock_download_chunk():
            nonlocal bytes_downloaded
            bytes_downloaded[0] += chunk_size
            
            if bytes_downloaded[0] < target_bytes * 0.5:
                raise ConnectionError("Download interrupted at {} MB".format(
                    bytes_downloaded[0] // (1024 * 1024)
                ))
            
            return {"bytes": chunk_size, "status": "complete"}
        
        result = handle_network_error(mock_download_chunk, max_retries=3)
        
        assert result is not None
        assert result.get("status") == "complete"
    
    def test_download_progress_tracking_with_errors(self):
        """
        Test that download progress is tracked correctly even with errors.
        """
        progress_log = []
        
        def mock_download_with_progress():
            progress_log.append(time.time())
            if len(progress_log) < 2:
                raise ConnectionError("Progress interrupted")
            return {"progress": 100, "complete": True}
        
        result = handle_network_error(mock_download_with_progress, max_retries=2)
        
        assert result is not None
        assert result.get("complete") is True
        assert len(progress_log) >= 2  # Should have retried

if __name__ == "__main__":
    pytest.main([__file__, "-v"])