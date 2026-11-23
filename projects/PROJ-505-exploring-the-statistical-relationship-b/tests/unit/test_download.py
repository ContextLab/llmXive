"""
Consolidated test that imports both ACE and NOAA download modules
and runs a simple end‑to‑end check that the raw files are written
and the parsed DataFrames contain the required columns.
"""

import pytest
from datetime import datetime
from pathlib import Path

from code.ingestion.download_ace import run_ingestion as run_ace
from code.ingestion.download_noaa import run_ingestion as run_noaa

def test_end_to_end_ace_and_noaa(tmp_path):
    """Run both ingestion scripts with mocked network calls and verify outputs."""
    start = datetime(2020, 1, 1)
    end = datetime(2020, 1, 2)

    ace_cfg = {
        "start_date": start,
        "end_date": end,
        "output_path": tmp_path / "ace.parquet",
    }
    noaa_cfg = {
        "start_date": start,
        "end_date": end,
        "output_path": tmp_path / "noaa.parquet",
    }

    # Mock ACE download
    from unittest import mock
    ace_csv = """timestamp,O/Fe,He/H,C/O,V,Bt,By,Bz
2020-01-01T00:00:00Z,0.1,0.05,0.2,400,5,0,0
2020-01-01T01:00:00Z,0.12,0.04,0.22,410,4.5,0.1,-0.1
"""
    with mock.patch("code.ingestion.download_ace._download_raw") as mock_ace_dl:
        mock_ace_dl.return_value = ace_csv.encode("utf-8")
        df_ace, src_ace = run_ace(ace_cfg)

    # Mock NOAA download
    kp_df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
        "Kp": [2, 3],
    })
    dst_df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
        "Dst": [-10, -12],
    })
    with mock.patch("code.ingestion.download_noaa.fetch_noaa_kp") as mock_kp, \
         mock.patch("code.ingestion.download_noaa.fetch_noaa_dst") as mock_dst:
        mock_kp.return_value = kp_df
        mock_dst.return_value = dst_df
        df_noaa, src_noaa = run_noaa(noaa_cfg)

    # Verify outputs
    assert ace_cfg["output_path"].exists()
    assert noaa_cfg["output_path"].exists()
    assert src_ace == "real"
    assert src_noaa == "real"
    # Basic column checks
    for col in ["O/Fe", "He/H", "C/O"]:
        assert col in df_ace.columns
    for col in ["Kp", "Dst"]:
        assert col in df_noaa.columns