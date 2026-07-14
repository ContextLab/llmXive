"""
Unit tests for ``code/url_security.py``.
"""

import pytest

from url_security import validate_download_url, secure_download

# Use a known good domain from the default whitelist.
GOOD_URL = "https://planck.gsfc.nasa.gov/data/maps/planck_map.fits"
BAD_SCHEME_URL = "http://planck.gsfc.nasa.gov/data/maps/planck_map.fits"
BAD_DOMAIN_URL = "https://malicious.example.com/evil.bin"

def test_validate_download_url_success():
    # Should return the original URL when everything is fine.
    assert validate_download_url(GOOD_URL) == GOOD_URL

def test_validate_download_url_insecure_scheme():
    with pytest.raises(ValueError, match="Insecure URL scheme"):
        validate_download_url(BAD_SCHEME_URL)

def test_validate_download_url_disallowed_domain():
    with pytest.raises(ValueError, match="Domain .* is not in the allowed download whitelist"):
        validate_download_url(BAD_DOMAIN_URL)

# The ``secure_download`` function internally uses ``utils.retry_download``.
# To keep the test fast and deterministic we monkey‑patch it.
def test_secure_download_calls_retry_download(monkeypatch):
    captured = {}

    def fake_retry_download(url, max_retries=3, base_delay=1.0):
        captured["url"] = url
        captured["max_retries"] = max_retries
        captured["base_delay"] = base_delay
        return b"dummy data"

    monkeypatch.setattr("utils.retry_download", fake_retry_download)

    data = secure_download(GOOD_URL, max_retries=5, base_delay=0.5)
    assert data == b"dummy data"
    assert captured["url"] == GOOD_URL
    assert captured["max_retries"] == 5
    assert captured["base_delay"] == 0.5

def test_secure_download_invalid_url(monkeypatch):
    # Ensure that validation happens before the download attempt.
    # ``retry_download`` should never be called for a bad URL.
    called = {"ran": False}

    def fake_retry_download(*args, **kwargs):
        called["ran"] = True
        return b""

    monkeypatch.setattr("utils.retry_download", fake_retry_download)

    with pytest.raises(ValueError):
        secure_download(BAD_DOMAIN_URL)

    assert not called["ran"], "retry_download should not be invoked for invalid URLs"