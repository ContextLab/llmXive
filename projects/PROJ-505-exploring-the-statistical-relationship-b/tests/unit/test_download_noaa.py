"""
Unit tests for NOAA data download.
The test mocks network responses for both Kp (JSON) and Dst (text) endpoints.
It verifies that:
- Raw files are written unchanged.
- Parsed DataFrames contain the required columns.
- The final merged DataFrame includes a data_source column set to "real".
"""

import io
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from unittest import mock

from code.ingestion.download_noaa import (
    _download_raw,
    fetch_noaa_kp,
    fetch_noaa_dst,
    run_ingestion,
)

# Helper checksum function
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@pytest.fixture
def kp_json():
    """Minimal JSON payload for Kp."""
    return [
        {"time_tag": "2020-01-01T00:00:00Z", "kp": 2},
        {"time_tag": "2020-01-01T01:00:00Z", "kp": 3},
    ]

@pytest.fixture
def dst_text():
    """Minimal Dst text file (fixed‑width)."""
    # Format: YYYYMMDD Dst
    return "20200101  -10\n20200101  -12\n"

def test_download_raw_writes_file(tmp_path, dst_text):
    """_download_raw should write raw bytes to disk."""
    url = "http://example.com/dst.txt"
    raw_path = tmp_path / "dst_raw.txt"

    with mock.patch("requests.get") as mock_get:
        mock_resp = mock.Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = dst_text.encode("utf-8")
        mock_get.return_value = mock_resp

        returned = _download_raw(url, raw_path)

    assert returned == dst_text.encode("utf-8")
    with open(raw_path, "rb") as f:
        file_bytes = f.read()
    assert file_bytes == dst_text.encode("utf-8")
    assert sha256(file_bytes) == sha256(dst_text.encode("utf-8"))

def test_fetch_noaa_kp_success(kp_json):
    """fetch_noaa_kp should return a DataFrame with timestamp and Kp."""
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)
    with mock.patch("requests.get") as mock_get:
        mock_resp = mock.Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = kp_json
        mock_get.return_value = mock_resp

        df = fetch_noaa_kp(start, end)

    assert list(df.columns) == ["timestamp", "Kp"]
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert df["Kp"].tolist() == [2, 3]

def test_fetch_noaa_dst_success(tmp_path, dst_text):
    """fetch_noaa_dst should parse the fixed‑width text file."""
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)
    with mock.patch("code.ingestion.download_noaa._download_raw") as mock_dl:
        mock_dl.return_value = dst_text.encode("utf-8")
        df = fetch_noaa_dst(start, end)

    assert list(df.columns) == ["timestamp", "Dst"]
    assert len(df) == 2
    # Verify timestamps parsed correctly
    expected_dates = [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-01")]
    pd.testing.assert_series_equal(df["timestamp"], pd.Series(expected_dates))
    # Verify Dst values
    assert df["Dst"].tolist() == [-10, -12]

def test_run_ingestion_writes_parquet(tmp_path, kp_json, dst_text):
    """run_ingestion should merge Kp and Dst, write parquet, and label source."""
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)
    config = {
        "start_date": start,
        "end_date": end,
        "output_path": tmp_path / "noaa.parquet",
    }

    # Patch network calls
    with mock.patch("code.ingestion.download_noaa.fetch_noaa_kp") as mock_kp, \
         mock.patch("code.ingestion.download_noaa.fetch_noaa_dst") as mock_dst:
        mock_kp.return_value = pd.DataFrame({
            "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
            "Kp": [2, 3],
        })
        mock_dst.return_value = pd.DataFrame({
            "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
            "Dst": [-10, -12],
        })

        df, source = run_ingestion(config)

    # Verify parquet file exists
    parquet_path = config["output_path"]
    assert parquet_path.exists()
    # Verify source label
    assert source == "real"
    # Verify merged columns
    assert set(df.columns) >= {"timestamp", "Kp", "Dst", "data_source"}
    assert df["data_source"].iloc[0] == "real"