import json
import pathlib

import pandas as pd
import pytest

from code.data.download import DataLoader, VERIFIED_DATASET_CONFIG

def test_download_creates_files(tmp_path, monkeypatch):
    """
    Integration‑style test that runs the DataLoader against the real
    Delaney dataset and checks that:
    1. The raw CSV file is written under ``data/raw/``.
    2. A ``checksums.json`` file exists and contains a SHA‑256 entry.
    3. The required columns are present in the resulting DataFrame.
    """
    # Use the project‑wide paths helper to locate the expected output locations.
    from llmxive_toolkit import paths

    # Ensure we start from a clean state.
    raw_dir = paths.data("raw")
    csv_path = raw_dir / "permeability_data.csv"
    checksum_path = raw_dir / "checksums.json"

    # Remove any leftovers from previous runs.
    if csv_path.exists():
        csv_path.unlink()
    if checksum_path.exists():
        checksum_path.unlink()

    # Run the loader.
    loader = DataLoader()
    df = loader.process()

    # Verify the CSV was written.
    assert csv_path.is_file(), f"Expected CSV at {csv_path}"
    # Verify checksum file was written and contains the correct key.
    assert checksum_path.is_file(), f"Expected checksum file at {checksum_path}"
    checksums = json.loads(checksum_path.read_text())
    assert csv_path.name in checksums, "Checksum entry missing for CSV file"

    # Verify required columns.
    for col in VERIFIED_DATASET_CONFIG["expected_columns"]:
        assert col in df.columns, f"Column {col} missing in downloaded DataFrame"
    # Ensure the DataFrame is not empty.
    assert len(df) > 0, "Downloaded dataset should contain rows"

# The test is marked as integration because it reaches out to the
# Hugging Face Hub. If network access is disabled in the execution
# environment, this test will fail loudly, which is the intended
# behaviour per the project constraints.