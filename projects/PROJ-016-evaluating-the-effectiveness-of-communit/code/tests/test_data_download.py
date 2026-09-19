import pytest
import time
import requests
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import fetch_with_backoff, MAX_RETRIES, BASE_DELAY

class TestDownloadRetryLogic:
    """Test the exponential backoff retry logic in download.py"""

    @patch('data.download.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        """Test that successful request on first attempt returns immediately"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        response = fetch_with_backoff("http://example.com/api")
        
        assert response.status_code == 200
        assert mock_get.call_count == 1

    @patch('data.download.requests.get')
    def test_retry_on_server_error(self, mock_get):
        """Test that server errors (5xx) trigger retries"""
        # First two attempts fail with 500, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "test"}

        mock_get.side_effect = [
            requests.HTTPError("500 Server Error"),
            requests.HTTPError("500 Server Error"),
            mock_response_success
        ]

        response = fetch_with_backoff("http://example.com/api")
        
        assert response.status_code == 200
        assert mock_get.call_count == 3

    @patch('data.download.requests.get')
    def test_no_retry_on_client_error(self, mock_get):
        """Test that client errors (4xx) do not trigger retries"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            fetch_with_backoff("http://example.com/api")
        
        assert mock_get.call_count == 1

    @patch('data.download.requests.get')
    def test_exponential_backoff_delays(self, mock_get):
        """Test that delays follow exponential backoff pattern"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        # First two attempts fail, third succeeds
        mock_get.side_effect = [
            requests.Timeout("Timeout"),
            requests.Timeout("Timeout"),
            mock_response
        ]

        # Track call times
        call_times = []
        original_sleep = time.sleep
        
        def mock_sleep(duration):
            call_times.append(duration)
            # Don't actually sleep in test
        
        with patch('data.download.time.sleep', side_effect=mock_sleep):
            fetch_with_backoff("http://example.com/api")

        # Should have 2 delays: BASE_DELAY * 2^0, BASE_DELAY * 2^1
        assert len(call_times) == 2
        assert call_times[0] == BASE_DELAY * (2 ** 0)  # 1.0 seconds
        assert call_times[1] == BASE_DELAY * (2 ** 1)  # 2.0 seconds

    @patch('data.download.requests.get')
    @patch('data.download.sys.exit')
    def test_exit_on_all_retries_failed(self, mock_exit, mock_get):
        """Test that sys.exit(1) is called after all retries fail"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        # Should raise SystemExit after MAX_RETRIES
        with pytest.raises(SystemExit) as exc_info:
            fetch_with_backoff("http://example.com/api")
        
        assert exc_info.value.code == 1
        assert mock_get.call_count == MAX_RETRIES
        mock_exit.assert_called_once_with(1)

    @patch('data.download.requests.get')
    @patch('data.download.sys.exit')
    def test_logs_error_to_run_log_on_failure(self, mock_exit, mock_get):
        """Test that error is logged to logs/run.log on failure"""
        import tempfile
        import os
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        # Create a temporary log file
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "logs" / "run.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Patch the log path
            with patch('data.download.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                # Also patch open to capture the write
                with patch('builtins.open', create=True) as mock_open_file:
                    mock_file = Mock()
                    mock_open_file.return_value.__enter__.return_value = mock_file
                    
                    try:
                        fetch_with_backoff("http://example.com/api")
                    except SystemExit:
                        pass
                    
                    # Verify that write was called with error message
                    assert mock_file.write.called
                    call_args = mock_file.write.call_args[0][0]
                    assert "CRITICAL" in call_args
                    assert "Failed to fetch" in call_args

class TestDownloadNoSyntheticFallback:
    """Verify that no synthetic data is generated on failure"""

    @patch('data.download.requests.get')
    @patch('data.download.sys.exit')
    def test_no_synthetic_data_generation(self, mock_exit, mock_get):
        """Ensure that failed fetch does not generate synthetic data"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        # Mock generate_synthetic_data to ensure it's never called
        with patch('data.download.generate_synthetic_data') as mock_gen:
            try:
                fetch_with_backoff("http://example.com/api")
            except SystemExit:
                pass
            
            # Verify synthetic generation was never called
            mock_gen.assert_not_called()

    def test_load_cbmrm_proxy_fails_without_file(self):
        """Test that loading CBNRM proxy fails loudly if file missing"""
        from data.download import load_cbmrm_proxy_data
        from pathlib import Path
        
        # Ensure the file doesn't exist
        proxy_path = Path("data/raw/cbnrm_proxy.csv")
        if proxy_path.exists():
            proxy_path.unlink()
        
        with pytest.raises(SystemExit) as exc_info:
            load_cbmrm_proxy_data()
        
        assert exc_info.value.code == 1