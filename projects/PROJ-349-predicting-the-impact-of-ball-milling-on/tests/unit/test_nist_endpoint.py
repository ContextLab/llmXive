"""
Unit test for the NIST endpoint validation logic (Task T060).

Ensures that the ``validate_nist_endpoint`` function raises a
``DataIngestionError`` only when the URL is unreachable, and otherwise
completes without exception.
"""
import pytest
import requests

from src.ingest.nist_repo import validate_nist_endpoint, NIST_DATA_URL
from src.exceptions import DataIngestionError

def test_validate_nist_endpoint_success():
    """
    The default NIST_DATA_URL points to a publicly accessible CSV on GitHub.
    The validation should succeed and raise no exception.
    """
    # The function internally performs a HEAD request; we let it run.
    # If the request fails (e.g., network outage), the test will surface the
    # problem, which is appropriate for CI.
    validate_nist_endpoint(NIST_DATA_URL)

def test_validate_nist_endpoint_failure(monkeypatch):
    """
    Simulate a failing request to ensure the function raises the correct
    exception type with a clear message.
    """
    def mock_head(*args, **kwargs):
        raise requests.RequestException("Connection error simulated")

    monkeypatch.setattr(requests, "head", mock_head)

    with pytest.raises(DataIngestionError) as exc_info:
        validate_nist_endpoint("http://invalid.example.com/nonexistent.csv")
    assert "could not reach" in str(exc_info.value) or "Connection error" in str(exc_info.value)