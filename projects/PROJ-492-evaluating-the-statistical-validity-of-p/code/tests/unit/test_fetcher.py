"""
Unit tests for the HTML Fetcher module.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from code.src.audit.fetcher import (
    fetch_url_with_retry,
    fetch_html_to_file,
    fetch_urls_batch,
    ingest_and_fetch,
    DEFAULT_TIMEOUT,
    MAX_RETRIES
)
from code.src.utils.logger import get_default_logger

logger = get_default_logger("test_fetcher")


class TestFetcherRetryLogic(unittest.TestCase):
    """Test retry logic and error handling."""

    @patch('code.src.audit.fetcher.requests.get')
    def test_fetch_success_on_first_attempt(self, mock_get):
        """Test successful fetch on first attempt."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        html, error = fetch_url_with_retry("http://example.com", max_retries=3)

        self.assertIsNone(error)
        self.assertEqual(html, "<html><body>Test</body></html>")
        mock_get.assert_called_once()

    @patch('code.src.audit.fetcher.requests.get')
    def test_fetch_success_after_retry(self, mock_get):
        """Test successful fetch after one retry."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Success</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        # First call raises timeout, second succeeds
        mock_get.side_effect = [
            Timeout("Connection timed out"),
            mock_response
        ]

        html, error = fetch_url_with_retry("http://example.com", max_retries=3, retry_delay=0.01)

        self.assertIsNone(error)
        self.assertEqual(html, "<html><body>Success</body></html>")
        self.assertEqual(mock_get.call_count, 2)

    @patch('code.src.audit.fetcher.requests.get')
    def test_fetch_failure_after_max_retries(self, mock_get):
        """Test failure after exhausting retries."""
        mock_get.side_effect = Timeout("Connection timed out")

        html, error = fetch_url_with_retry("http://example.com", max_retries=2, retry_delay=0.01)

        self.assertIsNotNone(error)
        self.assertIsNone(html)
        self.assertEqual(mock_get.call_count, 3)  # Initial + 2 retries

    @patch('code.src.audit.fetcher.requests.get')
    def test_no_retry_on_404(self, mock_get):
        """Test that 404 errors are not retried."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        from requests.exceptions import HTTPError
        mock_get.side_effect = HTTPError(response=mock_response)

        html, error = fetch_url_with_retry("http://example.com", max_retries=3)

        self.assertIsNotNone(error)
        self.assertIsNone(html)
        # Should only try once for 404
        self.assertEqual(mock_get.call_count, 1)


class TestFetchToFile(unittest.TestCase):
    """Test fetching and saving to file."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('code.src.audit.fetcher.requests.get')
    def test_save_html_to_file(self, mock_get):
        """Test saving HTML content to a file."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test Content</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        file_path, error = fetch_html_to_file(
            "http://example.com/test",
            self.output_dir,
            max_retries=1
        )

        self.assertIsNone(error)
        self.assertIsNotNone(file_path)
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.name.endswith(".html"))

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "<html><body>Test Content</body></html>")

    @patch('code.src.audit.fetcher.requests.get')
    def test_fetch_file_failure(self, mock_get):
        """Test failure when fetching fails."""
        mock_get.side_effect = Timeout("Connection timed out")

        file_path, error = fetch_html_to_file(
            "http://example.com/test",
            self.output_dir,
            max_retries=0
        )

        self.assertIsNotNone(error)
        self.assertIsNone(file_path)


class TestBatchFetching(unittest.TestCase):
    """Test batch fetching functionality."""

    @patch('code.src.audit.fetcher.fetch_html_to_file')
    def test_fetch_urls_batch(self, mock_fetch_file):
        """Test fetching multiple URLs."""
        mock_fetch_file.side_effect = [
            (Path("/fake/path1.html"), None),
            (None, Exception("Failed")),
            (Path("/fake/path3.html"), None)
        ]

        urls = ["http://example.com/1", "http://example.com/2", "http://example.com/3"]
        output_dir = Path("/fake/output")

        results = fetch_urls_batch(urls, output_dir, max_retries=0)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][0], "http://example.com/1")
        self.assertIsNotNone(results[0][1])
        self.assertIsNone(results[0][2])

        self.assertEqual(results[1][0], "http://example.com/2")
        self.assertIsNone(results[1][1])
        self.assertIsNotNone(results[1][2])


class TestIngestAndFetch(unittest.TestCase):
    """Test reading URLs from CSV and fetching."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_urls_from_csv(self):
        """Test reading URLs from a CSV file."""
        csv_path = self.temp_path / "urls.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write("url\n")
            f.write("http://example.com/1\n")
            f.write("http://example.com/2\n")

        # Mock the fetch function to avoid network calls
        with patch('code.src.audit.fetcher.fetch_urls_batch') as mock_batch:
            mock_batch.return_value = [
                ("http://example.com/1", Path("/fake/1.html"), None),
                ("http://example.com/2", Path("/fake/2.html"), None)
            ]

            results = ingest_and_fetch(csv_path, Path("/fake/output"), max_retries=0)

            self.assertEqual(len(results), 2)
            mock_batch.assert_called_once()
            # Verify the URLs passed to fetch_urls_batch
            call_args = mock_batch.call_args[0][0]
            self.assertEqual(call_args, ["http://example.com/1", "http://example.com/2"])

    def test_read_plain_csv(self):
        """Test reading URLs from a CSV without headers."""
        csv_path = self.temp_path / "plain_urls.csv"
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("http://example.com/1\n")
            f.write("http://example.com/2\n")

        with patch('code.src.audit.fetcher.fetch_urls_batch') as mock_batch:
            mock_batch.return_value = []
            ingest_and_fetch(csv_path, Path("/fake/output"), max_retries=0)

            call_args = mock_batch.call_args[0][0]
            self.assertEqual(call_args, ["http://example.com/1", "http://example.com/2"])


if __name__ == "__main__":
    unittest.main()
