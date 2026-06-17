"""Unit tests for the KnotAtlas downloader."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
from code.download.knot_atlas_loader import (
    KnotRecord,
    download_knot_atlas_data,
    save_raw_data,
    verify_downloaded_record,
)


@pytest.fixture
def fake_records():
    """Return a small list of dictionaries mimicking ``database_knotinfo`` output."""
    return [
        {
            "name": "3_1",
            "crossing_number": 3,
            "braid_index": 2,
            "volume": 2.02988,
            "alternating": True,
        },
        {
            "name": "4_1",
            "crossing_number": 4,
            "braid_index": 3,
            "volume": 3.66386,
            "alternating": True,
        },
    ]


def test_download_uses_database_knotinfo(monkeypatch, fake_records):
    """The downloader should call ``database_knotinfo.link_list`` and wrap results."""

    with mock.patch("code.download.knot_atlas_loader.dk.link_list", return_value=fake_records):
        records = download_knot_atlas_data()
        assert isinstance(records, list)
        assert all(isinstance(r, KnotRecord) for r in records)
        assert records[0].name == "3_1"
        assert records[1].crossing_number == 4


def test_verify_downloaded_record():
    good = KnotRecord(
        name="5_2",
        crossing_number=5,
        braid_index=3,
        volume=1.234,
        alternating=False,
    )
    bad = KnotRecord(
        name="",
        crossing_number=0,
        braid_index=0,
        volume=None,
        alternating=None,
    )
    assert verify_downloaded_record(good) is True
    assert verify_downloaded_record(bad) is False


def test_save_raw_data_writes_json(tmp_path: Path):
    """Ensure ``save_raw_data`` writes a JSON file that can be re‑loaded."""
    records = [
        KnotRecord(
            name="6_1",
            crossing_number=6,
            braid_index=4,
            volume=4.123,
            alternating=True,
        )
    ]
    out_file = tmp_path / "raw.json"
    save_raw_data(records, out_file)

    # Verify file exists
    assert out_file.is_file()

    # Verify JSON is well‑formed and matches the original data
    with out_file.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert isinstance(loaded, list) and len(loaded) == 1
    assert loaded[0]["name"] == "6_1"
    assert loaded[0]["crossing_number"] == 6
    assert loaded[0]["braid_index"] == 4
