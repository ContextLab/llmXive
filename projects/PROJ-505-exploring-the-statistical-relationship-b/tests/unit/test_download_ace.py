"""
Unit tests for ACE data download.
The test patches the network request to return a minimal CSV payload
containing the required columns. It then verifies that:
- The raw file is written unchanged.
- The parsed DataFrame contains the expected columns.
- The checksum of the raw file matches the checksum of the written bytes.
"""

import io
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from unittest import mock

# Import the module under test
from code.ingestion.download_ace import (
    _download_raw,
    _parse_ace_csv,
    fetch_ace_data,
    run_ingestion,
)

# Helper to compute SHA‑256 checksum
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@pytest.fixture
def sample_csv_bytes():
    """A minimal CSV payload with required columns."""
    csv = """timestamp,O/Fe,He/H,C/O,V,Bt,By,Bz
2020-01-01T00:00:00Z,0.1,0.05,0.2,400,5,0,0
2020-01-01T01:00:00Z,0.12,0.04,0.22,410,4.5,0.1,-0.1
"""
    return csv.encode("utf-8")

def test_download_raw_writes_file(tmp_path, sample_csv_bytes):
    """_download_raw should write the exact bytes to the given path."""
    url = "http://example.com/ace.csv"
    raw_path = tmp_path / "ace_raw.csv"

    with mock.patch("requests.get") as mock_get:
        mock_resp = mock.Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = sample_csv_bytes
        mock_get.return_value = mock_resp

        returned = _download_raw(url, raw_path)

    # Verify returned content matches input
    assert returned == sample_csv_bytes
    # Verify file exists and content matches
    with open(raw_path, "rb") as f:
        file_bytes = f.read()
    assert file_bytes == sample_csv_bytes
    # Verify checksum
    assert sha256(file_bytes) == sha256(sample_csv_bytes)

def test_parse_ace_csv_success(sample_csv_bytes):
    """_parse_ace_csv should return a DataFrame with correct columns."""
    df = _parse_ace_csv(sample_csv_bytes)
    expected_cols = {"timestamp", "O/Fe", "He/H", "C/O", "V", "Bt", "By", "Bz"}
    assert set(df.columns) == expected_cols
    # Timestamp column should be datetime dtype
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

def test_fetch_ace_data_success(tmp_path, sample_csv_bytes):
    """fetch_ace_data should download, write raw file, and parse."""
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)
    with mock.patch("code.ingestion.download_ace._download_raw") as mock_dl:
        mock_dl.return_value = sample_csv_bytes
        df = fetch_ace_data(start, end)
    # Verify DataFrame shape
    assert len(df) == 2
    # Verify required columns present
    for col in ["O/Fe", "He/H", "C/O", "timestamp"]:
        assert col in df.columns

def test_run_ingestion_creates_parquet(tmp_path):
    """run_ingestion should write a parquet file and add data_source column."""
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)
    config = {
        "start_date": start,
        "end_date": end,
        "output_path": tmp_path / "ace.parquet",
    }
    # Patch network call to return sample CSV bytes
    sample = """timestamp,O/Fe,He/H,C/O,V,Bt,By,Bz
2020-01-01T00:00:00Z,0.1,0.05,0.2,400,5,0,0
2020-01-01T01:00:00Z,0.12,0.04,0.22,410,4.5,0.1,-0.1
"""
    with mock.patch("code.ingestion.download_ace._download_raw") as mock_dl:
        mock_dl.return_value = sample.encode("utf-8")
        df, source = run_ingestion(config)

    # Parquet file should exist
    parquet_path = config["output_path"]
    assert parquet_path.exists()
    # Data source label should be "real"
    assert source == "real"
    # DataFrame should contain data_source column
    assert "data_source" in df.columns
    assert df["data_source"].iloc[0] == "real"