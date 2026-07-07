"""
Unit tests for the download module.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import requests

# Import the function to test
from code.data.download import download_try_data, calculate_md5, exponential_backoff_retry
from code.utils.logging import DataPipelineLog

class MockLogger:
    """Mock logger for testing."""
    def info(self, msg, **kwargs):
        pass
    def error(self, msg, **kwargs):
        pass
    def warning(self, msg, **kwargs):
        pass

def test_calculate_md5():
    """Test MD5 calculation on a temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_path = f.name
    
    try:
        checksum = calculate_md5(temp_path)
        assert len(checksum) == 32
        assert isinstance(checksum, str)
    finally:
        os.remove(temp_path)

@patch('code.data.download.requests.get')
def test_download_success(mock_get):
    """Test successful download."""
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"test data"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MockLogger()
        path = download_try_data(logger, tmpdir)
        
        assert os.path.exists(path)
        mock_get.assert_called_once()

@patch('code.data.download.requests.get')
def test_download_checksum_mismatch(mock_get):
    """Test download with checksum mismatch."""
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"test data"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MockLogger()
        # Provide a wrong checksum
        with pytest.raises(RuntimeError, match="Checksum mismatch"):
            download_try_data(logger, tmpdir, expected_checksum="wrong_checksum")

@patch('code.data.download.requests.get')
def test_download_retry_logic(mock_get):
    """Test that download retries on failure."""
    mock_get.side_effect = [
        requests.exceptions.RequestException("Network Error"),
        requests.exceptions.RequestException("Network Error"),
        MagicMock(iter_content=lambda: [b"data"], raise_for_status=MagicMock())
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MockLogger()
        # Should succeed after 2 retries
        path = download_try_data(logger, tmpdir)
        assert mock_get.call_count == 3
        assert os.path.exists(path)

@patch('code.data.download.requests.get')
def test_download_max_retries_exceeded(mock_get):
    """Test that download fails after max retries."""
    mock_get.side_effect = requests.exceptions.RequestException("Persistent Error")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MockLogger()
        with pytest.raises(RuntimeError, match="Failed to download"):
            download_try_data(logger, tmpdir)

@patch('code.data.download.requests.get')
def test_download_404_simulation(mock_get):
    """Test retry logic specifically for 404 Not Found errors."""
    # Simulate two 404 errors followed by a successful response
    mock_404_response = MagicMock()
    mock_404_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=MagicMock(status_code=404))
    
    mock_success_response = MagicMock()
    mock_success_response.iter_content.return_value = [b"valid data"]
    mock_success_response.raise_for_status = MagicMock()
    
    mock_get.side_effect = [
        mock_404_response,
        mock_404_response,
        mock_success_response
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MockLogger()
        # Should succeed after retrying on 404s
        path = download_try_data(logger, tmpdir)
        
        # Verify we called the mock 3 times (2 failures + 1 success)
        assert mock_get.call_count == 3
        assert os.path.exists(path)
        
        # Verify the file content
        with open(path, 'rb') as f:
            content = f.read()
            assert content == b"valid data"

@patch('code.data.download.requests.get')
def test_download_404_max_retries(mock_get):
    """Test that 404 errors are retried and eventually fail if max retries exceeded."""
    mock_404_response = MagicMock()
    mock_404_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=MagicMock(status_code=404))
    
    # Always return 404
    mock_get.side_effect = mock_404_response

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MockLogger()
        # Should fail after max retries
        with pytest.raises(RuntimeError, match="Failed to download"):
            download_try_data(logger, tmpdir)
        
        # Verify we retried the expected number of times (default is 3)
        assert mock_get.call_count == 3