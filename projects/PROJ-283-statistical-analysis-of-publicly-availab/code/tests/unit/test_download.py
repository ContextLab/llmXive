"""
Unit tests for the download module (T008e).
Tests exponential backoff retry logic, URL verification, and error handling.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.download import (
    retry_fetch_with_backoff,
    DataFetchError,
    load_selected_ids,
    verify_url_reachability
)


class TestExponentialBackoffRetry:
    """Test the exponential backoff retry logic."""

    def test_success_on_first_attempt(self):
        """Test that a successful function returns immediately."""
        mock_func = Mock(return_value="success")
        
        result = retry_fetch_with_backoff(mock_func, max_retries=3, base_delay=0.01)
        
        assert result == "success"
        assert mock_func.call_count == 1

    def test_success_after_retries(self):
        """Test that a function succeeds after some failures."""
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"
        
        with patch('time.sleep'):  # Skip actual sleep in tests
            result = retry_fetch_with_backoff(flaky_function, max_retries=5, base_delay=0.01)
        
        assert result == "success"
        assert call_count == 3

    def test_failure_after_max_retries(self):
        """Test that DataFetchError is raised after max retries."""
        def failing_function():
            raise ConnectionError("Persistent network error")
        
        with patch('time.sleep'):  # Skip actual sleep in tests
            with pytest.raises(DataFetchError) as exc_info:
                retry_fetch_with_backoff(failing_function, max_retries=3, base_delay=0.01)
        
        assert "Download failed after 3 retries" in str(exc_info.value)
        assert exc_info.type == DataFetchError

    def test_rate_limit_handling(self):
        """Test that rate limit errors are handled correctly."""
        def rate_limited_function():
            from requests.exceptions import HTTPError
            raise HTTPError(response=Mock(status_code=429))
        
        with patch('time.sleep'):
            with pytest.raises(DataFetchError) as exc_info:
                retry_fetch_with_backoff(rate_limited_function, max_retries=2, base_delay=0.01)
        
        assert "Download failed" in str(exc_info.value)


class TestLoadSelectedIds:
    """Test the load_selected_ids function."""

    def test_load_ids_success(self, tmp_path):
        """Test loading IDs from a file."""
        ids_file = tmp_path / "selected_ids.txt"
        ids_content = "game1\n\ngame2\n  game3  \n"
        ids_file.write_text(ids_content)
        
        ids = load_selected_ids(str(ids_file))
        
        assert len(ids) == 3
        assert "game1" in ids
        assert "game2" in ids
        assert "game3" in ids

    def test_load_ids_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_selected_ids("nonexistent_file.txt")

    def test_load_ids_empty_file(self, tmp_path):
        """Test loading from an empty file."""
        ids_file = tmp_path / "empty_ids.txt"
        ids_file.write_text("")
        
        ids = load_selected_ids(str(ids_file))
        
        assert len(ids) == 0


class TestVerifyUrlReachability:
    """Test the URL verification function."""

    @patch('src.data.download.load_dataset_builder')
    def test_url_reachable(self, mock_builder):
        """Test that a reachable dataset returns True."""
        mock_builder.return_value = MagicMock()
        
        result = verify_url_reachability("https://example.com")
        
        assert result is True

    @patch('src.data.download.load_dataset_builder')
    def test_url_unreachable(self, mock_builder):
        """Test that an unreachable dataset returns False."""
        mock_builder.side_effect = Exception("Dataset not found")
        
        result = verify_url_reachability("https://example.com")
        
        assert result is False
