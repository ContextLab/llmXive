"""
Unit tests for download module.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import time
import requests

from src.data.download import (
    exponential_backoff_retry,
    verify_url_reachability,
    download_from_huggingface,
    download_from_url,
    download_chess_data,
    INITIAL_BACKOFF,
    MAX_RETRIES,
    BACKOFF_MULTIPLIER
)


class TestExponentialBackoffRetry:
    def test_success_on_first_attempt(self):
        """Test that a successful function returns immediately."""
        mock_func = MagicMock(return_value="success")
        
        result = exponential_backoff_retry(mock_func, max_retries=3)
        
        assert result == "success"
        mock_func.assert_called_once()

    def test_retry_on_failure(self):
        """Test that function retries on failure."""
        mock_func = MagicMock(side_effect=[
            requests.exceptions.ConnectionError("Fail"),
            "success"
        ])
        
        with patch('src.data.download.time.sleep'):
            result = exponential_backoff_retry(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 2

    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""
        mock_func = MagicMock(side_effect=requests.exceptions.ConnectionError("Fail"))
        
        with patch('src.data.download.time.sleep'):
            with pytest.raises(requests.exceptions.ConnectionError):
                exponential_backoff_retry(mock_func, max_retries=2)
        
        assert mock_func.call_count == 3  # Initial + 2 retries


class TestVerifyUrlReachability:
    def test_reachable_url(self):
        """Test that a reachable URL returns True."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('src.data.download.requests.head', return_value=mock_response):
            result = verify_url_reachability("https://example.com")
        
        assert result is True

    def test_unreachable_url(self):
        """Test that an unreachable URL returns False."""
        with patch('src.data.download.requests.head', side_effect=requests.exceptions.RequestException):
            result = verify_url_reachability("https://invalid-url.com")
        
        assert result is False


class TestDownloadFromHuggingface:
    @patch('src.data.download.load_dataset')
    @patch('src.data.download.Path')
    def test_download_success(self, mock_path, mock_load_dataset):
        """Test successful download from HuggingFace."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=100)
        mock_dataset.select = MagicMock(return_value=mock_dataset)
        mock_load_dataset.return_value = mock_dataset
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_path_instance)
        
        result = download_from_huggingface("/tmp/test", subset=10)
        
        assert result == mock_path_instance
        mock_load_dataset.assert_called_once()
        mock_dataset.to_parquet.assert_called_once()


class TestDownloadChesData:
    def test_invalid_source(self):
        """Test that invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid dataset_source"):
            download_chess_data(dataset_source="invalid")

    @patch('src.data.download.download_from_huggingface')
    def test_huggingface_source(self, mock_download):
        """Test HuggingFace download path."""
        mock_download.return_value = Path("/tmp/test.parquet")
        
        result = download_chess_data(dataset_source="huggingface")
        
        assert result == Path("/tmp/test.parquet")
        mock_download.assert_called_once()

    @patch('src.data.download.verify_url_reachability')
    @patch('src.data.download.download_from_url')
    def test_url_source_unreachable(self, mock_download, mock_verify):
        """Test URL download when URL is unreachable."""
        mock_verify.return_value = False
        
        with pytest.raises(ValueError, match="Dataset URL is unreachable"):
            download_chess_data(dataset_source="url")

    @patch('src.data.download.FALLBACK_URL', "https://example.com/data.pgn")
    @patch('src.data.download.verify_url_reachability')
    @patch('src.data.download.download_from_url')
    def test_url_source_success(self, mock_download, mock_verify):
        """Test successful URL download."""
        mock_verify.return_value = True
        mock_download.return_value = Path("/tmp/data.pgn")
        
        result = download_chess_data(dataset_source="url")
        
        assert result == Path("/tmp/data.pgn")
        mock_verify.assert_called_once()
        mock_download.assert_called_once()
