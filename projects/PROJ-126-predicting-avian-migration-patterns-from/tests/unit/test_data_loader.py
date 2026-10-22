"""
Unit tests for the eBird data loader.
"""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

# Ensure the code directory is on the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import load_ebird_data, DATA_RAW, EBIRD_OUTPUT_FILE, CHECKSUMS_FILE

def test_load_ebird_data_creates_files(tmp_path, monkeypatch):
    """
    Test that load_ebird_data downloads the sample, writes CSV and checksum,
    and returns a DataFrame with the expected columns.
    """
    # Use the project's DATA_RAW directory
    raw_dir = DATA_RAW
    # Ensure a clean state
    if raw_dir.exists():
        for f in raw_dir.iterdir():
            f.unlink()
    else:
        raw_dir.mkdir(parents=True)

    df = load_ebird_data()
    # Verify DataFrame is not empty and contains required columns
    assert not df.empty
    required_cols = {"species_code", "duration_min", "num_observers", "distance_km",
                     "latitude", "longitude", "year"}
    assert required_cols.issubset(set(df.columns))

    # Verify CSV file exists
    csv_path = raw_dir / EBIRD_OUTPUT_FILE
    assert csv_path.is_file()
    # Verify checksum file exists and contains entry for CSV
    checksum_path = raw_dir / CHECKSUMS_FILE
    assert checksum_path.is_file()
    with open(checksum_path, "r") as f:
        checksums = json.load(f)
    assert EBIRD_OUTPUT_FILE in checksums
    # Verify stored checksum matches actual file checksum
    from data_loader import calculate_sha256
    actual_hash = calculate_sha256(csv_path)
    assert checksums[EBIRD_OUTPUT_FILE] == actual_hash