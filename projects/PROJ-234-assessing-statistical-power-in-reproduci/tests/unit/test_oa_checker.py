"""
Unit tests for ``code.utils.oa_checker``.
"""
from unittest import mock

import pytest

from code.utils.oa_checker import is_open_access, DataFetchError

# ----------------------------------------------------------------------
def test_known_oa_domains():
    # Domains that are whitelisted should return True without any network call.
    assert is_open_access("https://arxiv.org/abs/1234.5678")
    assert is_open_access("https://doi.org/10.1000/xyz123")
    assert is_open_access("https://pubmedcentral.nih.gov/articles/PMC1234567")

# ----------------------------------------------------------------------
def test_head_request_success(monkeypatch):
    mock_response = mock.Mock()
    mock_response.ok = True
    mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}

    monkeypatch.setattr("requests.head", lambda *a, **kw: mock_response)

    assert is_open_access("https://example.com/open-access-paper")

# ----------------------------------------------------------------------
def test_head_request_non_oa(monkeypatch):
    mock_response = mock.Mock()
    mock_response.ok = True
    mock_response.headers = {"Content-Type": "application/octet-stream"}

    monkeypatch.setattr("requests.head", lambda *a, **kw: mock_response)

    assert not is_open_access("https://example.com/paywalled")

# ----------------------------------------------------------------------
def test_head_request_failure(monkeypatch):
    # Simulate a network error.
    monkeypatch.setattr(
        "requests.head",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("network error")),
    )

    with pytest.raises(DataFetchError):
        is_open_access("https://example.com/bad")
