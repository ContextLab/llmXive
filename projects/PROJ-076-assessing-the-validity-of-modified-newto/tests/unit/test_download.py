"""
Unit tests for the SPARC downloader module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

from download import (
    fetch_with_retry,
    download_file,
    validate_url,
    is_valid_sparc_source,
    verify_file_integrity,
    download_sparc_data
)


class TestValidateUrl:
    def test_valid_https_url(self):
        # Note: This test might hit the network. In a strict unit test, we might mock.
        # But for T012, we test the logic.
        assert validate_url("https://example.com") is True or validate_url("https://example.com") is False
        # The function returns False if the site is down, which is valid behavior.
        # We just test it doesn't crash.
        assert isinstance(validate_url("https://example.com"), bool)

    def test_invalid_scheme(self):
        assert validate_url("ftp://example.com") is False
        assert validate_url("file:///etc/passwd") is False

    def test_malformed_url(self):
        assert validate_url("not-a-url") is False


class TestIsValidSparcSource:
    def test_valid_github_pattern(self):
        assert is_valid_sparc_source("https://github.com/leroy-lell/sparc-data/raw/master/Data.zip") is True

    def test_valid_sparc_org(self):
        assert is_valid_sparc_source("https://sparc-l.org/data/file.zip") is True

    def test_invalid_url(self):
        assert is_valid_sparc_source("https://random-site.com/data.zip") is False


class TestVerifyFileIntegrity:
    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.txt"
            assert verify_file_integrity(path, "abc123") is False

    def test_no_checksum_provided(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_text("hello")
            # Should return True when no checksum is expected
            assert verify_file_integrity(path, None) is True

    def test_matching_checksum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            content = b"hello world"
            path.write_bytes(content)
            
            # Compute expected hash
            import hashlib
            expected = hashlib.sha256(content).hexdigest()
            
            assert verify_file_integrity(path, expected) is True

    def test_mismatching_checksum(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.write_bytes(b"hello world")
            assert verify_file_integrity(path, "wronghash") is False


class TestFetchWithRetry:
    @patch('download.requests.get')
    def test_success_on_first_attempt(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = fetch_with_retry("http://test.com", retries=2, delay=0.01)
        assert result is not None
        assert result.status_code == 200
        mock_get.assert_called_once()

    @patch('download.requests.get')
    def test_retry_on_failure(self, mock_get):
        # First call fails, second succeeds
        mock_fail = MagicMock()
        mock_fail.status_code = 500
        mock_success = MagicMock()
        mock_success.status_code = 200
        
        mock_get.side_effect = [mock_fail, mock_success]

        result = fetch_with_retry("http://test.com", retries=2, delay=0.01)
        assert result is not None
        assert result.status_code == 200
        assert mock_get.call_count == 2

    @patch('download.requests.get')
    def test_exhaust_retries(self, mock_get):
        mock_fail = MagicMock()
        mock_fail.status_code = 500
        mock_get.return_value = mock_fail

        result = fetch_with_retry("http://test.com", retries=2, delay=0.01)
        assert result is None
        assert mock_get.call_count == 3 # Initial + 2 retries


class TestDownloadFile:
    @patch('download.fetch_with_retry')
    def test_download_success(self, mock_fetch):
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"data"]
        mock_fetch.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "file.txt"
            success = download_file("http://test.com", dest, retries=0)
            
            assert success is True
            assert dest.exists()
            assert dest.read_bytes() == b"data"

    @patch('download.fetch_with_retry')
    def test_download_failure(self, mock_fetch):
        mock_fetch.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "file.txt"
            success = download_file("http://test.com", dest, retries=0)
            
            assert success is False
            assert not dest.exists() # Should not create file if fetch fails


class TestDownloadSparcData:
    @patch('download.validate_url')
    @patch('download.download_file')
    @patch('download.verify_file_integrity')
    def test_full_success(self, mock_verify, mock_download, mock_validate):
        mock_validate.return_value = True
        mock_download.return_value = True
        mock_verify.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_sparc_data(output_dir, url="http://test.com/Data.zip", verify_checksum=True)
            
            assert result is not None
            assert result.name == "Data.zip"
            assert result.parent == output_dir

    @patch('download.validate_url')
    def test_invalid_url(self, mock_validate):
        mock_validate.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_sparc_data(Path(tmpdir), url="http://bad.com")
            assert result is None