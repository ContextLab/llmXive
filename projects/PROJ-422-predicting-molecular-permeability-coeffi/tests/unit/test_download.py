"""
Unit test for ``code/data/download.py``.

The test verifies that:
1. The raw CSV file is written under ``data/raw/``.
2. A ``checksums.json`` file exists and contains a SHA‑256 entry.
3. The required columns (``smiles`` and ``permeability``) are present.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from code.data.download import DataLoader

def test_download_creates_files():
    """
    Executes the DataLoader against the real dataset specified in
    ``config/selected_dataset.yaml`` and checks that the outputs satisfy
    the task requirements.
    """
    # Ensure a clean state – remove any previous artefacts.
    raw_dir = Path("data") / "raw"
    # Use the filename from config
    import yaml
    with open("config/selected_dataset.yaml", "r") as f:
        config = yaml.safe_load(f)
    csv_name = config.get("filename", "dataset.csv")
    csv_path = raw_dir / csv_name
    checksum_path = raw_dir / "checksums.json"

    if csv_path.exists():
        csv_path.unlink()
    if checksum_path.exists():
        checksum_path.unlink()

    # Run the loader.
    loader = DataLoader()
    loader.process()

    # Verify the CSV was written.
    assert csv_path.is_file(), f"Expected CSV at {csv_path}"
    # Verify checksum file was written and contains the correct key.
    assert checksum_path.is_file(), f"Expected checksum file at {checksum_path}"
    checksums = json.loads(checksum_path.read_text())
    assert csv_path.name in checksums, "Checksum entry missing for CSV file"

    # Verify required columns.
    df = pd.read_csv(csv_path)
    required = ["smiles", "permeability"]
    # Column check should be case-insensitive
    actual_cols = [c.lower() for c in df.columns]
    for col in required:
        assert col in actual_cols, f"Column {col} missing in downloaded DataFrame"
    # Ensure the DataFrame is not empty.
    assert len(df) > 0, "Downloaded dataset should contain rows"