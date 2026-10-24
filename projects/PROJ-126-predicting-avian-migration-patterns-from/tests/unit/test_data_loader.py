"""
Unit tests for the eBird data loader (code/data_loader.py).
These tests verify that the loader writes the expected output files
and that the checksum file is correctly generated.
"""
import json
from pathlib import Path

import pytest

# Import the loader functions
from data_loader import load_ebird_data, EBIRD_OUTPUT_FILE, CHECKSUMS_FILE

def test_ebird_output_exists(tmp_path, monkeypatch):
    """
    Ensure that after running the loader, the CSV file exists and is non‑empty.
    The test runs the loader in a temporary directory to avoid polluting the
    repository data folder.
    """
    # Redirect the DATA_RAW constant to a temporary directory
    from code import config

    monkeypatch.setattr(config, "DATA_RAW", tmp_path, raising=False)

    # Run the loader (this will download the real dataset)
    df = load_ebird_data()

    # Verify CSV exists
    csv_path = tmp_path / EBIRD_OUTPUT_FILE
    assert csv_path.is_file(), "CSV output file was not created."

    # Verify it contains rows
    assert csv_path.stat().st_size > 0, "CSV output file is empty."
    assert len(df) > 0, "Returned DataFrame is empty."

def test_checksum_file_created(tmp_path, monkeypatch):
    """
    Verify that a checksum JSON file is created and contains the SHA‑256
    hash for the generated CSV.
    """
    from code import config

    monkeypatch.setattr(config, "DATA_RAW", tmp_path, raising=False)

    # Run the loader
    _ = load_ebird_data()

    checksum_path = tmp_path / CHECKSUMS_FILE
    assert checksum_path.is_file(), "Checksum JSON file was not created."

    # Load JSON and check that the key matches the CSV filename
    data = json.loads(checksum_path.read_text())
    assert EBIRD_OUTPUT_FILE in data, "CSV filename missing from checksum JSON."
    # The value should be a 64‑character hex string
    assert isinstance(data[EBIRD_OUTPUT_FILE], str) and len(data[EBIRD_OUTPUT_FILE]) == 64
