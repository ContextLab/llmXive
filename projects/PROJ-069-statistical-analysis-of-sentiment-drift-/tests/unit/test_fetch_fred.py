"""
Unit tests for ``code.ingest.fetch_fred``.

The tests avoid real network calls by monkey‑patching ``fredapi.Fred``.
They verify:
* The script raises a clear error when the ``FRED_API_KEY`` environment
  variable is missing.
* When a mocked ``Fred`` client returns a tiny but valid series, the
  expected CSV files are written, checksums are recorded and the download
  log contains three entries.
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Ensure the environment does not contain a FRED key unless the test sets it."""
    monkeypatch.delenv("FRED_API_KEY", raising=False)


def test_missing_api_key(monkeypatch):
    """The script must abort with a helpful message if the API key is absent."""
    from code.ingest import fetch_fred

    # The helper in ``config`` raises ValueError when the key is missing.
    with pytest.raises(ValueError, match="FRED_API_KEY environment variable is required"):
        fetch_fred.main()


def _mock_fred_series(series_id):
    """Return a tiny pandas Series for any requested series."""
    dates = pd.date_range(start="2000-01-01", periods=5, freq="Q")
    values = pd.Series([1, 2, 3, 4, 5], index=dates, name=series_id)
    return values


class MockFred:
    """Minimal mock of ``fredapi.Fred`` used by the script."""

    def __init__(self, *_, **__):
        pass

    def get_series(self, series_id):
        return _mock_fred_series(series_id)


def test_successful_download(monkeypatch, tmp_path):
    """
    Verify that the script creates the three CSV files, updates the checksum
    file and writes the download log.
    """
    # ------------------------------------------------------------------
    # Arrange – provide a dummy API key and patch the Fred client
    # ------------------------------------------------------------------
    monkeypatch.setenv("FRED_API_KEY", "dummy-key")
    monkeypatch.setattr("code.ingest.fetch_fred.Fred", MockFred)

    # Ensure a clean workspace – the test runner starts with an empty
    # ``data/checksums.json`` if it does not exist.
    checksums_path = paths.data("checksums.json")
    if checksums_path.exists():
        checksums_path.unlink()

    # ------------------------------------------------------------------
    # Act
    # ------------------------------------------------------------------
    from code.ingest import fetch_fred

    fetch_fred.main()

    # ------------------------------------------------------------------
    # Assert – CSV files exist and contain a header row
    # ------------------------------------------------------------------
    for name in ("fred_gdp.csv", "fred_unrate.csv", "fred_consumer_confidence.csv"):
        csv_path = paths.data("raw", "fred", name)
        assert csv_path.is_file(), f"{csv_path} was not created"
        # Simple sanity check: first line must be the header
        with csv_path.open("r", encoding="utf-8") as f:
            header = f.readline().strip()
        assert header == "date,value"

    # ------------------------------------------------------------------
    # Assert – checksums.json contains entries for the three files
    # ------------------------------------------------------------------
    with checksums_path.open("r", encoding="utf-8") as f:
        checksums = json.load(f)
    expected_keys = {
        str(paths.data("raw", "fred", "fred_gdp.csv").relative_to(paths.root)),
        str(paths.data("raw", "fred", "fred_unrate.csv").relative_to(paths.root)),
        str(paths.data("raw", "fred", "fred_consumer_confidence.csv").relative_to(paths.root)),
    }
    assert expected_keys.issubset(set(checksums.keys()))

    # ------------------------------------------------------------------
    # Assert – download log contains three entries with correct URLs
    # ------------------------------------------------------------------
    log_path = paths.results("fred_download_log.json")
    assert log_path.is_file()
    with log_path.open("r", encoding="utf-8") as f:
        log_content = json.load(f)
    assert isinstance(log_content, list) and len(log_content) == 3
    series_ids = {entry["series_id"] for entry in log_content}
    assert series_ids == {"GDP", "UNRATE", "CSCICP03"}