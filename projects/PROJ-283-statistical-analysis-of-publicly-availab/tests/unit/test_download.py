import pytest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.download import (
    DataFetchError,
    load_selected_ids,
    retry_fetch_with_backoff,
    verify_url_reachability,
    verify_mirror_metadata
)

class TestExponentialBackoffRetry:
    """Tests for the retry_fetch_with_backoff function."""
    
    def test_retry_logic(self):
        """Test that retry logic implements exponential backoff correctly."""
        url = "https://example.com/data"
        max_retries = 3
        base_delay = 0.1  # Short delay for testing
        
        call_times = []
        
        # Mock requests.get to fail twice then succeed
        with patch('src.data.download.requests.get') as mock_get:
            # First two calls fail, third succeeds
            mock_response_fail = Mock()
            mock_response_fail.status_code = 500
            mock_response_fail.reason = "Internal Server Error"
            mock_response_fail.iter_content.return_value = []
            
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.iter_content.return_value = [b"success"]
            
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timeout"),
                requests.exceptions.Timeout("Timeout"),
                mock_response_success
            ]
            
            # Capture time between calls
            start_time = time.time()
            chunks = list(retry_fetch_with_backoff(url, max_retries, base_delay))
            end_time = time.time()
            
            # Verify we got the success chunk
            assert len(chunks) > 0
            assert chunks[0] == "success"
            
            # Verify that we made 3 attempts (2 failures + 1 success)
            assert mock_get.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that DataFetchError is raised after max retries."""
        url = "https://example.com/data"
        max_retries = 2
        base_delay = 0.1
        
        with patch('src.data.download.requests.get') as mock_get:
            # All calls fail
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            
            with pytest.raises(DataFetchError) as exc_info:
                list(retry_fetch_with_backoff(url, max_retries, base_delay))
            
            assert "Download failed after 2 retries" in str(exc_info.value.reason)
            assert mock_get.call_count == max_retries
    
    def test_rate_limiting_handling(self):
        """Test that 429 status code raises appropriate error."""
        url = "https://example.com/data"
        
        with patch('src.data.download.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.reason = "Too Many Requests"
            mock_get.return_value = mock_response
            
            with pytest.raises(DataFetchError) as exc_info:
                list(retry_fetch_with_backoff(url))
            
            assert "Rate limit exceeded" in str(exc_info.value.reason)

class TestLoadSelectedIds:
    """Tests for the load_selected_ids function."""
    
    def test_load_from_file(self, tmp_path):
        """Test loading IDs from a file."""
        ids_file = tmp_path / "selected_ids.txt"
        ids_content = "game1\n\ngame2\ngame3\n"
        ids_file.write_text(ids_content)
        
        ids = load_selected_ids(ids_file)
        
        assert ids == ["game1", "game2", "game3"]
    
    def test_empty_file_raises_error(self, tmp_path):
        """Test that an empty file raises ValueError."""
        ids_file = tmp_path / "selected_ids.txt"
        ids_file.write_text("")
        
        with pytest.raises(ValueError, match="empty"):
            load_selected_ids(ids_file)
    
    def test_file_not_found_raises_error(self, tmp_path):
        """Test that a missing file raises FileNotFoundError."""
        ids_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            load_selected_ids(ids_file)

class TestVerifyUrlReachability:
    """Tests for the verify_url_reachability function."""
    
    @patch('src.data.download.requests.head')
    def test_url_reachable(self, mock_head):
        """Test that a reachable URL returns True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        assert verify_url_reachability("https://example.com") is True
    
    @patch('src.data.download.requests.head')
    def test_url_not_reachable(self, mock_head):
        """Test that an unreachable URL returns False."""
        mock_head.side_effect = requests.exceptions.Timeout()
        
        assert verify_url_reachability("https://example.com") is False

class TestVerifyMirrorMetadata:
    """Tests for the verify_mirror_metadata function."""
    
    @patch('src.data.download.verify_url_reachability')
    @patch('src.data.download.load_dataset')
    def test_metadata_present(self, mock_load_dataset, mock_verify_url):
        """Test successful metadata verification."""
        mock_verify_url.return_value = True
        
        # Mock dataset with metadata
        mock_dataset = Mock()
        mock_dataset.__getitem__.return_value = iter([
            {"fen": "start", "pgn": "1. e4"},
            {"fen": "middle", "pgn": "2. Nf3"}
        ])
        mock_load_dataset.return_value = mock_dataset
        
        result = verify_mirror_metadata("https://example.com/data")
        assert result is True
    
    @patch('src.data.download.verify_url_reachability')
    def test_url_unreachable(self, mock_verify_url):
        """Test that unreachable URL raises DataFetchError."""
        mock_verify_url.return_value = False
        
        with pytest.raises(DataFetchError, match="URL unreachable"):
            verify_mirror_metadata("https://example.com/data")
    
    @patch('src.data.download.verify_url_reachability')
    @patch('src.data.download.load_dataset')
    def test_metadata_missing(self, mock_load_dataset, mock_verify_url):
        """Test that missing metadata raises DataFetchError."""
        mock_verify_url.return_value = True
        
        # Mock dataset without metadata
        mock_dataset = Mock()
        mock_dataset.__getitem__.return_value = iter([
            {"data": "no metadata"},
            {"data": "still no metadata"}
        ])
        mock_load_dataset.return_value = mock_dataset
        
        with pytest.raises(DataFetchError, match="metadata missing"):
            verify_mirror_metadata("https://example.com/data")