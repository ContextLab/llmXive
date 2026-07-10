"""
Unit tests for the Fetcher module (T019).
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

# Mock requests before importing the module to avoid real network calls in tests
import sys
from unittest.mock import Mock

# We need to mock requests globally
sys.modules['requests'] = MagicMock()
sys.modules['requests.exceptions'] = MagicMock()

from code.src.audit.fetcher import (
    fetch_url_with_retry,
    fetch_html_to_file,
    fetch_urls_batch,
    ingest_and_fetch,
    MAX_RETRIES,
    TIMEOUT_SECONDS
)
from code.src.utils.logger import get_default_logger

logger = get_default_logger("test_fetcher")


@patch('code.src.audit.fetcher.requests.get')
def test_fetch_url_with_retry_success(mock_get):
    """Test successful fetch on first attempt."""
    mock_response = MagicMock()
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    url = "http://example.com/test"
    result = fetch_url_with_retry(url)

    assert result == "<html><body>Test</body></html>"
    mock_get.assert_called_once()


@patch('code.src.audit.fetcher.requests.get')
def test_fetch_url_with_retry_timeout(mock_get):
    """Test retry logic on timeout."""
    from requests.exceptions import Timeout as RequestsTimeout

    mock_get.side_effect = [RequestsTimeout("Timeout"), "<html>Success</html>"]
    # Note: The side_effect above is slightly tricky because the second call returns a string directly
    # We need to mock the response object for the second call
    mock_get.side_effect = [
        RequestsTimeout("Timeout"),
        MagicMock(text="<html>Success</html>", status_code=200, raise_for_status=MagicMock())
    ]

    url = "http://example.com/test"
    result = fetch_url_with_retry(url)

    assert result == "<html>Success</html>"
    assert mock_get.call_count == 2


@patch('code.src.audit.fetcher.requests.get')
def test_fetch_url_with_retry_failure(mock_get):
    """Test that fetch returns None after max retries."""
    from requests.exceptions import RequestException

    mock_get.side_effect = RequestException("Network error")

    url = "http://example.com/test"
    result = fetch_url_with_retry(url)

    assert result is None
    assert mock_get.call_count == MAX_RETRIES


@patch('code.src.audit.fetcher.fetch_url_with_retry')
def test_fetch_html_to_file(mock_fetch):
    """Test saving HTML to a file."""
    mock_fetch.return_value = "<html><body>Test</body></html>"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        url = "http://example.com/test"

        result = fetch_html_to_file(url, output_dir)

        assert result is not None
        url_out, file_path = result
        assert url_out == url
        assert file_path.exists()
        assert file_path.suffix == ".html"
        with open(file_path, 'r') as f:
            content = f.read()
        assert content == "<html><body>Test</body></html>"


@patch('code.src.audit.fetcher.fetch_html_to_file')
def test_fetch_urls_batch(mock_fetch_file):
    """Test fetching a batch of URLs."""
    mock_fetch_file.side_effect = [
        ("http://a.com", Path("/tmp/a.html")),
        None,  # Failed fetch
        ("http://b.com", Path("/tmp/b.html"))
    ]

    urls = ["http://a.com", "http://fail.com", "http://b.com"]
    results = fetch_urls_batch(urls)

    assert len(results) == 2
    assert results[0][0] == "http://a.com"
    assert results[1][0] == "http://b.com"


def test_ingest_and_fetch_missing_file(caplog):
    """Test handling of missing input CSV file."""
    result = ingest_and_fetch("nonexistent.csv")
    assert result == []
    assert "not found" in caplog.text.lower()


@patch('code.src.audit.fetcher.fetch_urls_batch')
def test_ingest_and_fetch(mock_batch_fetch):
    """Test reading URLs from CSV and fetching."""
    mock_batch_fetch.return_value = [("http://test.com", Path("/tmp/test.html"))]

    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("url\nhttp://test.com\n")
        csv_path = f.name

    try:
        results = ingest_and_fetch(csv_path)
        assert len(results) == 1
        assert results[0][0] == "http://test.com"
    finally:
        os.unlink(csv_path)
