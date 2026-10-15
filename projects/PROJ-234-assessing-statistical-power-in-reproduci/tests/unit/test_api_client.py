"""
Unit tests for ``code.utils.api_client``.
"""

import json
from unittest import mock

import pytest

from code.utils.api_client import DataFetchError, get_openml_json

# ----------------------------------------------------------------------
# Helper to build a dummy ``requests.Response``‑like object.
# ----------------------------------------------------------------------
class _DummyResponse:
    def __init__(self, status_code: int, json_data=None):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        if self._json_data is None:
            raise json.JSONDecodeError("Expecting value", "", 0)
        return self._json_data

    @property
    def ok(self):
        return 200 <= self.status_code < 300

# ----------------------------------------------------------------------
def test_successful_fetch(monkeypatch):
    dummy = _DummyResponse(200, {"data": "ok"})
    monkeypatch.setattr("requests.get", lambda *a, **kw: dummy)

    result = get_openml_json("datasets/list", max_retries=0)
    assert result == {"data": "ok"}

# ----------------------------------------------------------------------
def test_rate_limit_retry(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        # First two attempts: 429, third: 200
        if len(calls) < 3:
            return _DummyResponse(429)
        return _DummyResponse(200, {"final": True})

    monkeypatch.setattr("requests.get", fake_get)

    result = get_openml_json("datasets/list", max_retries=5, initial_delay=0, max_delay=0)
    assert result == {"final": True}
    assert len(calls) == 3

# ----------------------------------------------------------------------
def test_non_retryable_error(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **kw: _DummyResponse(500))

    with pytest.raises(DataFetchError) as excinfo:
        get_openml_json("datasets/list", max_retries=1, initial_delay=0, max_delay=0)
    assert excinfo.value.status_code == 500

# ----------------------------------------------------------------------
def test_invalid_json(monkeypatch):
    # Return a 200 but with unparsable JSON.
    monkeypatch.setattr(
        "requests.get", lambda *a, **kw: _DummyResponse(200, json_data=None)
    )

    with pytest.raises(DataFetchError) as excinfo:
        get_openml_json("datasets/list", max_retries=0)
    assert excinfo.value.status_code == 200
