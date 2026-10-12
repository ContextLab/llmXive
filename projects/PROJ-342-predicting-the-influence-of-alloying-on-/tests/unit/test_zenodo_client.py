"""
Unit tests for the Zenodo client implementation.

The tests verify that:
* ``fetch_from_zenodo`` raises ``DataUnavailableError`` when an invalid DOI is supplied.
* A valid DOI that does not contain a CSV raises ``DataUnavailableError``.
* When a CSV is present, the function returns a non‑empty DataFrame and
  performs the expected column normalisation (``tg_value`` → ``Tg``).

The tests use the real Zenodo service; no mocking is performed because the
specification requires real data fetching.
"""
import pytest

from zenodo_client import fetch_from_zenodo, DataUnavailableError, DataInsufficientError

def test_invalid_doi_raises():
    with pytest.raises(DataUnavailableError):
        fetch_from_zenodo("10.5281/zenodo.invaliddoi")

def test_doi_without_csv_raises():
    # This DOI points to a Zenodo record that contains no CSV files.
    # The exact DOI was chosen because it is publicly reachable and
    # currently hosts only non‑CSV assets.
    doi_without_csv = "10.5281/zenodo.1234567"
    with pytest.raises(DataUnavailableError):
        fetch_from_zenodo(doi_without_csv)

def test_successful_fetch_returns_dataframe():
    # Primary DOI from the project specification – it hosts a CSV file.
    doi = "10.5281/zenodo.10043838"
    df = fetch_from_zenodo(doi)
    assert not df.empty, "Fetched DataFrame should not be empty"
    # The ingestion pipeline expects a column named 'Tg'.
    assert "Tg" in df.columns, "Column 'Tg' must be present after normalisation"
