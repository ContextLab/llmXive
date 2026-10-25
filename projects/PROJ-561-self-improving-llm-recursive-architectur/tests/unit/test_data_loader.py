"""
Unit tests for the data loader utilities, focusing on URL verification and
the exponential back‑off wrapper.
"""
import pytest
from pipeline.loader import verify_urls, exponential_backoff

@exponential_backoff
def flaky_head(url):
    """A dummy function that simulates a transient failure on the first call."""
    if not hasattr(flaky_head, "called"):
        flaky_head.called = True
        raise RuntimeError("Transient failure")
    return True

def test_verify_urls_success(monkeypatch):
    # Mock requests.head to always succeed
    def mock_head(url, timeout=5):
        class Resp:
            status_code = 200
            def raise_for_status(self):
                pass
        return Resp()
    monkeypatch.setattr("requests.head", mock_head)
    assert verify_urls(["http://example.com"])

def test_verify_urls_failure(monkeypatch):
    # Mock requests.head to always raise an HTTPError
    def mock_head(url, timeout=5):
        raise requests.HTTPError("404 Not Found")
    monkeypatch.setattr("requests.head", mock_head)
    with pytest.raises(ValueError):
        verify_urls(["http://nonexistent.invalid"])

def test_exponential_backoff_decorator(monkeypatch):
    # Ensure that the decorator retries once and then succeeds
    result = flaky_head("http://dummy")
    assert result is True
    # Subsequent call should succeed without raising
    result2 = flaky_head("http://dummy")
    assert result2 is True