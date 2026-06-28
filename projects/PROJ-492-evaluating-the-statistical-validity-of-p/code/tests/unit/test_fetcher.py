"""Unit tests for HTML fetcher module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.src.audit.fetcher import (
    fetch_url_with_retry,
    fetch_html_to_file,
    fetch_urls_batch,
    ingest_and_fetch,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from code.src.utils.logger import get_default_logger


class TestFetchUrlWithRetry:
    """Tests for fetch_url_with_retry function."""

    def test_successful_fetch(self):
        """Test successful URL fetch."""
        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body>Test</body></html>"
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            success, html, error = fetch_url_with_retry("http://example.com")

            assert success is True
            assert html is not None
            assert "<html>" in html
            assert error is None

    def test_timeout_error(self):
        """Test timeout error handling."""
        from requests.exceptions import Timeout

        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            mock_get.side_effect = Timeout("Request timed out")

            success, html, error = fetch_url_with_retry(
                "http://example.com",
                timeout=1,
                max_retries=1
            )

            assert success is False
            assert html is None
            assert error is not None
            assert "Timeout" in error

    def test_connection_error_retry(self):
        """Test that connection errors trigger retries."""
        from requests.exceptions import ConnectionError

        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            # First two attempts fail, third succeeds
            mock_get.side_effect = [
                ConnectionError("Connection failed"),
                ConnectionError("Connection failed"),
                MagicMock(text="<html>OK</html>", status_code=200, raise_for_status=MagicMock())
            ]

            success, html, error = fetch_url_with_retry(
                "http://example.com",
                timeout=1,
                max_retries=2
            )

            assert success is True
            assert html is not None
            assert mock_get.call_count == 3

    def test_http_error(self):
        """Test HTTP error handling."""
        from requests.exceptions import HTTPError

        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
            mock_get.return_value = mock_response

            success, html, error = fetch_url_with_retry("http://example.com")

            assert success is False
            assert html is None
            assert error is not None
            assert "404" in error


class TestFetchHtmlToFile:
    """Tests for fetch_html_to_file function."""

    def test_fetch_and_save(self):
        """Test fetching and saving HTML to file."""
        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body>Test Content</body></html>"
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                success, filepath, error = fetch_html_to_file(
                    "http://example.com/test",
                    output_dir
                )

                assert success is True
                assert filepath is not None
                assert filepath.exists()
                assert "example.com" in filepath.name
                assert filepath.suffix == ".html"
                assert "Test Content" in filepath.read_text()
                assert error is None

    def test_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html>Test</html>"
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / "new" / "subdir"
                success, filepath, error = fetch_html_to_file(
                    "http://example.com/test",
                    output_dir
                )

                assert success is True
                assert output_dir.exists()


class TestFetchUrlsBatch:
    """Tests for fetch_urls_batch function."""

    def test_batch_fetch(self):
        """Test fetching multiple URLs."""
        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            def mock_response(*args, **kwargs):
                m = MagicMock()
                m.text = "<html>OK</html>"
                m.status_code = 200
                m.raise_for_status = MagicMock()
                return m

            mock_get.return_value = mock_response()

            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                urls = [
                    "http://example.com/1",
                    "http://example.com/2",
                    "http://test.com/3"
                ]

                results = fetch_urls_batch(urls, output_dir)

                assert len(results) == 3
                for url, success, filepath, error in results:
                    assert success is True
                    assert filepath is not None
                    assert filepath.exists()
                    assert error is None


class TestIngestAndFetch:
    """Tests for ingest_and_fetch function."""

    def test_ingest_and_fetch_from_csv(self):
        """Test reading URLs from CSV and fetching."""
        import csv

        with patch('code.src.audit.fetcher.requests.get') as mock_get:
            def mock_response(*args, **kwargs):
                m = MagicMock()
                m.text = "<html>OK</html>"
                m.status_code = 200
                m.raise_for_status = MagicMock()
                return m

            mock_get.return_value = mock_response()

            with tempfile.TemporaryDirectory() as tmpdir:
                input_csv = Path(tmpdir) / "urls_deduped.csv"
                output_dir = Path(tmpdir) / "raw"

                # Create input CSV
                with open(input_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['url'])
                    writer.writerow(['http://example.com/1'])
                    writer.writerow(['http://example.com/2'])

                results = ingest_and_fetch(input_csv, output_dir)

                assert len(results) == 2
                for url, success, filepath, error in results:
                    assert success is True
                    assert filepath is not None


class TestFetchUrlConstants:
    """Tests for fetcher module constants."""

    def test_default_timeout(self):
        """Test default timeout is reasonable."""
        assert DEFAULT_TIMEOUT >= 10
        assert DEFAULT_TIMEOUT <= 60

    def test_max_retries(self):
        """Test max retries is positive."""
        assert MAX_RETRIES >= 1
        assert MAX_RETRIES <= 10

    def test_retry_delay(self):
        """Test retry delay is positive."""
        assert RETRY_DELAY > 0
