"""
Unit tests for security hardening (T038).
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils import sanitize_url, sanitize_file_path, get_project_root_path, get_retry_session, load_data_from_api
from requests.exceptions import RequestException

class TestUrlSanitization:
    def test_valid_https_url(self):
        url = "https://example.com/data"
        sanitized = sanitize_url(url)
        assert sanitized == url
        assert sanitized.startswith("https://")

    def test_valid_http_url(self):
        url = "http://example.com/data"
        sanitized = sanitize_url(url)
        assert sanitized == url

    def test_invalid_protocol(self):
        url = "ftp://example.com/data"
        with pytest.raises(ValueError, match="Disallowed protocol"):
            sanitize_url(url)

    def test_empty_url(self):
        with pytest.raises(ValueError, match="non-empty"):
            sanitize_url("")

    def test_path_traversal_in_url(self):
        url = "https://example.com/../../../etc/passwd"
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_url(url)

class TestPathSanitization:
    def test_valid_relative_path(self):
        path = "data/raw/test.csv"
        sanitized = sanitize_file_path(path)
        assert sanitized.is_absolute()
        assert "data/raw/test.csv" in str(sanitized)

    def test_valid_absolute_path_within_project(self):
        root = get_project_root_path()
        path = root / "data" / "raw" / "test.csv"
        sanitized = sanitize_file_path(str(path))
        assert sanitized == path.resolve()

    def test_path_traversal_attempt(self):
        path = "../../etc/passwd"
        with pytest.raises(ValueError, match="path traversal"):
            sanitize_file_path(path)

    def test_path_outside_project(self):
        path = "/etc/passwd"
        with pytest.raises(ValueError, match="outside the project root"):
            sanitize_file_path(path)

    def test_empty_path(self):
        with pytest.raises(ValueError, match="non-empty"):
            sanitize_file_path("")

class TestRetrySession:
    def test_session_creation(self):
        session = get_retry_session()
        assert session is not None
        assert len(session.adapters) == 2  # http and https

    def test_session_retries_configured(self):
        session = get_retry_session(retries=5)
        adapter = session.adapters['https://']
        assert adapter.max_retries.total == 5

class TestDataLoading:
    def test_load_data_from_api_invalid_url(self):
        with pytest.raises(ValueError):
            load_data_from_api("ftp://invalid.com")

    def test_load_data_from_api_timeout(self):
        # This test might be slow, so we just check it raises an exception
        # In a real CI environment, we might mock the request
        with pytest.raises((RequestException, ValueError)):
            load_data_from_api("https://httpbin.org/delay/10", timeout=1)
