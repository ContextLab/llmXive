"""
Unit tests for the download utilities.

The tests verify that the request dictionaries are correctly formed and that
the helper functions raise informative errors when the CDS client cannot be
instantiated (e.g., when the API key is missing).  Actual network calls are
**not** performed; they are mocked using ``unittest.mock``.
"""

import builtins
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
from src.data.download import (
    download_era5_geopotential,
    download_era5_ivt,
    _client,
    _years_list,
)


@pytest.fixture(autouse=True)
def mock_cds_client(monkeypatch):
    """
    Patch ``cdsapi.Client`` with a mock that records the retrieve call.
    """
    mock_client = mock.MagicMock()
    monkeypatch.setattr("src.data.download.cdsapi.Client", lambda: mock_client)
    return mock_client


def test_years_list():
    """Ensure the year list spans 1979‑2023 inclusive."""
    years = _years_list()
    assert years[0] == 1979
    assert years[-1] == 2023
    assert len(years) == 2023 - 1979 + 1


def test_download_ivt_builds_correct_path(tmp_path, mock_cds_client):
    """download_era5_ivt should call the CDS client with the correct dataset."""
    out_path = tmp_path / "my_ivt.nc"
    result_path = download_era5_ivt(out_path)

    # The function should return the exact path we passed in
    assert result_path == out_path

    # Verify that retrieve was called with the expected dataset name
    mock_cds_client.retrieve.assert_called_once()
    args, kwargs = mock_cds_client.retrieve.call_args
    assert args[0] == "reanalysis-era5-pressure-levels"
    # The request dict must contain the variable name
    request = args[1]
    assert "integrated_water_vapor_transport" in request["variable"]


def test_download_geopotential_builds_correct_path(tmp_path, mock_cds_client):
    """download_era5_geopotential should call the CDS client with the correct dataset."""
    out_path = tmp_path / "my_z500.nc"
    result_path = download_era5_geopotential(out_path)

    assert result_path == out_path
    mock_cds_client.retrieve.assert_called_once()
    args, kwargs = mock_cds_client.retrieve.call_args
    assert args[0] == "reanalysis-era5-pressure-levels"
    request = args[1]
    assert request["variable"] == "geopotential"
    assert request["pressure_level"] == "500"


def test_client_failure_raises_runtime_error(monkeypatch):
    """If the CDS client cannot be created, a RuntimeError should be raised."""
    def bad_client():
        raise Exception("auth failure")

    monkeypatch.setattr("src.data.download.cdsapi.Client", bad_client)

    with pytest.raises(RuntimeError) as excinfo:
        _client()
    assert "Failed to create a CDS API client" in str(excinfo.value)