"""
Unit tests for the OpenML API client wrapper.
"""

import pytest

# Import the public function from the utils package
from utils.api_client import fetch_top_classification_datasets, DataFetchError


def test_fetch_top_classification_datasets_returns_list():
    """
    The function should return a list (possibly empty) of dataset dicts.
    We request a small number to keep the test fast and network‑light.
    """
    datasets = fetch_top_classification_datasets(max_datasets=5, max_retries=2)
    assert isinstance(datasets, list)
    # Each entry should be a dict with at least a ``dataset_id`` key
    for ds in datasets:
        assert isinstance(ds, dict)
        assert "dataset_id" in ds


def test_fetch_raises_DataFetchError_on_bad_url(monkeypatch):
    """
    Simulate a permanent 429 response to ensure the wrapper raises
    ``DataFetchError`` after exhausting retries.
    """
    class DummyResponse:
        status_code = 429
        def raise_for_status(self):
            raise Exception("429")

    def dummy_get(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("requests.get", dummy_get)

    with pytest.raises(DataFetchError):
        fetch_top_classification_datasets(max_datasets=1, max_retries=1)
