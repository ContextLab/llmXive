"""Basic smoke‑tests for the Knot Atlas loader."""

import json
from pathlib import Path

import pytest

# Import the module under test
from download.knot_atlas_loader import (
    download_knot_atlas_data,
    save_raw_data,
    parse_knot_atlas_data,
    save_cleaned_data,
    KnotRecord,
)


@pytest.fixture(scope="module")
def raw_records(tmp_path_factory):
    """Download a small subset of records for testing purposes."""
    # The real download pulls all ~13k records – that's acceptable for a unit
    # test in this environment because the package is cached and fast.
    records = download_knot_atlas_data()
    assert isinstance(records, list) and len(records) > 0
    return records


def test_save_raw_and_load(tmp_path: Path, raw_records):
    """Ensure that the raw JSON round‑trips correctly."""
    raw_path = tmp_path / "raw.json"
    save_raw_data(raw_records, raw_path)
    assert raw_path.is_file()

    with raw_path.open() as f:
        loaded = json.load(f)
    assert loaded == raw_records


def test_parse_and_save_cleaned(tmp_path: Path, raw_records):
    """Parse the raw dicts and write a CSV; verify column consistency."""
    cleaned_path = tmp_path / "cleaned.csv"
    cleaned = parse_knot_atlas_data(raw_records)
    assert all(isinstance(r, KnotRecord) for r in cleaned)
    save_cleaned_data(cleaned, cleaned_path)
    assert cleaned_path.is_file()

    # Simple sanity‑check: CSV header must contain the expected columns.
    with cleaned_path.open() as f:
        header = f.readline().strip()
    expected = "name,crossing_number,braid_index,alternating,volume"
    assert header == expected


def test_round_trip_consistency(tmp_path: Path, raw_records):
    """Full pipeline smoke test – raw → cleaned → CSV → re‑load."""
    raw_path = tmp_path / "raw.json"
    cleaned_path = tmp_path / "cleaned.csv"
    save_raw_data(raw_records, raw_path)
    cleaned = parse_knot_atlas_data(raw_records)
    save_cleaned_data(cleaned, cleaned_path)

    # Reload CSV and compare a few fields with the original objects.
    import csv
    with cleaned_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == len(cleaned)
    # Compare the first row as a spot‑check.
    first_original = cleaned[0]
    first_row = rows[0]
    assert first_row["name"] == first_original.name
    # ``None`` values are written as empty strings in CSV.
    assert (
        (first_row["crossing_number"] == "" and first_original.crossing_number is None)
        or int(first_row["crossing_number"]) == first_original.crossing_number
    )


# The following sanity checks are deliberately lightweight; they ensure that
# the public helpers exist and behave without raising unexpected exceptions.
def test_verification_helpers():
    from download.knot_atlas_loader import (
        verify_downloaded_record,
        verify_retry_logic,
        verify_partial_caching,
    )

    sample = {
        "name": "3_1",
        "crossing_number": 3,
        "braid_index": 2,
        "alternating": True,
        "volume": 2.02988,
    }
    verify_downloaded_record(sample)
    verify_retry_logic(attempts=1, max_attempts=3)
    verify_partial_caching(cached=False)