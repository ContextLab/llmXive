import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.data.utils import fetch_with_backoff, fetch_with_backoff_bytes, FetchError


class TestFetchWithBackoff:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_successful_fetch_creates_file(self, temp_dir):
        """Test that a successful fetch creates the destination file."""
        mock_url = "https://httpbin.org/json"
        dest = temp_dir / "test_data.json"

        result = fetch_with_backoff(mock_url, dest, max_retries=1)

        assert result == dest
        assert dest.exists()
        assert dest.stat().st_size > 0

    def test_fetch_error_after_retries(self, temp_dir):
        """Test that FetchError is raised after max retries on failure."""
        mock_url = "https://invalid.url.that.does.not.exist/test"
        dest = temp_dir / "fail.json"

        with pytest.raises(FetchError) as exc_info:
            fetch_with_backoff(mock_url, dest, max_retries=2, base_delay=0.1)

        assert "Failed to fetch" in str(exc_info.value)
        assert exc_info.value.last_exception is not None

    @patch("src.data.utils.urllib.request.urlretrieve")
    def test_retry_logic_on_failure(self, mock_urlretrieve, temp_dir):
        """Test that retries happen with exponential backoff."""
        mock_urlretrieve.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            None,  # Success on 3rd attempt
        ]

        mock_url = "http://example.com/data"
        dest = temp_dir / "retry_test.txt"

        start = time.time()
        result = fetch_with_backoff(
            mock_url, dest, max_retries=3, base_delay=0.05, max_delay=0.1
        )
        elapsed = time.time() - start

        assert result == dest
        assert mock_urlretrieve.call_count == 3
        # Should take some time due to backoff (2 retries with ~0.05s delay)
        assert elapsed > 0.05

class TestFetchWithBackoffBytes:
    def test_successful_bytes_fetch(self):
        """Test fetching raw bytes from a URL."""
        mock_url = "https://httpbin.org/json"

        data = fetch_with_backoff_bytes(mock_url, max_retries=1)

        assert isinstance(data, bytes)
        assert len(data) > 0

    @patch("src.data.utils.urllib.request.urlopen")
    def test_bytes_retry_logic(self, mock_urlopen):
        """Test retry logic for bytes fetching."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"test data"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        # First two calls fail, third succeeds
        mock_urlopen.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            mock_response,
        ]

        with patch("src.data.utils.time.sleep"):  # Speed up test
            data = fetch_with_backoff_bytes(
                "http://example.com", max_retries=3, base_delay=0.01
            )

        assert data == b"test data"
        assert mock_urlopen.call_count == 3

    def test_fetch_error_bytes(self):
        """Test FetchError for bytes fetch."""
        with pytest.raises(FetchError):
            fetch_with_backoff_bytes(
                "https://invalid.url.that.does.not.exist", max_retries=1, base_delay=0.01
            )