"""
Unit tests for the eBird data loader.
"""
import os
import json
import pandas as pd
from pathlib import Path

from code.data_loader import load_ebird_data, DATA_RAW, EBIRD_OUTPUT_FILE, CHECKSUMS_FILE, calculate_sha256

def test_load_ebird_creates_files(tmp_path, monkeypatch):
    """
    Verify that the loader creates the CSV and checksum file,
    and that the checksum matches the file content.
    """
    # Redirect DATA_RAW to a temporary directory for isolation
    monkeypatch.setattr('code.data_loader.DATA_RAW', tmp_path, raising=False)

    # Run the loader (this will stream from the real dataset)
    df = load_ebird_data()

    csv_path = tmp_path / EBIRD_OUTPUT_FILE
    checksum_path = tmp_path / CHECKSUMS_FILE

    assert csv_path.is_file(), "CSV output file was not created"
    assert checksum_path.is_file(), "Checksum JSON file was not created"

    # Verify that the checksum stored matches the actual file hash
    with open(checksum_path, "r") as f:
        checksums = json.load(f)
    stored_hash = checksums.get(EBIRD_OUTPUT_FILE)
    actual_hash = calculate_sha256(csv_path)
    assert stored_hash == actual_hash, "Stored checksum does not match file hash"

    # Basic sanity check on the dataframe
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # All rows should be for species SRUT and within the required year range
    assert df["species_code"].eq("SRUT").all()
    assert df["year"].between(2015, 2022).all()
    # Verify the required columns exist
    required_cols = {"species_code", "year", "latitude", "longitude", "duration_min", "num_observers", "distance_km"}
    assert required_cols.issubset(set(df.columns))
