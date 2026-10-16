"""
Unit tests for the OA checker utility.
"""

import pytest

from utils.oa_checker import is_open_access


def test_known_oa_domain_returns_true(monkeypatch):
    """
    For a known OA domain (arxiv) we expect ``True``.
    The test monkey‑patches ``requests.head`` to avoid a real network call.
    """
    class DummyResponse:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}

    def dummy_head(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("requests.head", dummy_head)

    assert is_open_access("https://arxiv.org/abs/2101.00001") is True


def test_unknown_domain_returns_false():
    """
    URLs that are not on the known OA list should be reported as ``False``
    without performing any network request.
    """
    assert is_open_access("https://example.com/somepaper") is False


def test_malformed_url_returns_false():
    """
    An empty or malformed URL should safely return ``False``.
    """
    assert is_open_access("") is False
    assert is_open_access("not a url") is False
