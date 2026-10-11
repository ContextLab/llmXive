import json
import os
from pathlib import Path

import pandas as pd

from download import download_all, DATA_RAW_DIR, CHECKSUMS_FILE

def test_download_all_creates_files_and_metadata(tmp_path, monkeypatch):
    """
    Executes the download_all function and verifies that:
    - Each dataset CSV exists in data/raw/
    - A corresponding metadata JSON file exists
    - The number of rows in each CSV does not exceed the cap (5,000)
    - The checksums manifest contains an entry for each dataset
    """
    # Ensure the test runs in an isolated temporary directory
    project_root = Path(__file__).resolve().parents[2]  # project root two levels up
    # Monkeypatch the DATA_RAW_DIR to point inside the temporary directory
    monkeypatch.setattr("download.DATA_RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr("download.CHECKSUMS_FILE", tmp_path / "checksums.txt")

    # Run the download routine
    download_all()

    # Verify CSV files and metadata
    expected_keys = {"oqmd_band_gap", "oqmd_formation_energy", "aflow_thermal_conductivity"}
    for key in expected_keys:
        cfg = {
            "oqmd_band_gap": "oqmd_band_gap.csv",
            "oqmd_formation_energy": "oqmd_formation_energy.csv",
            "aflow_thermal_conductivity": "aflow_thermal_conductivity.csv"
        }[key]

        csv_path = tmp_path / "raw" / cfg
        meta_path = tmp_path / "raw" / f"{key}_metadata.json"

        assert csv_path.is_file(), f"CSV file missing for {key}"
        assert meta_path.is_file(), f"Metadata JSON missing for {key}"

        df = pd.read_csv(csv_path)
        assert len(df) <= 5000, f"{key} exceeds cap of 5,000 rows"

        # Validate metadata content
        with open(meta_path, "r") as f:
            meta = json.load(f)
        assert meta["dataset_key"] == key
        assert meta["filename"] == cfg
        assert meta["num_samples"] == len(df)
        assert meta["cap_applied"] == 5000

    # Verify checksum manifest entries
    manifest_content = (tmp_path / "checksums.txt").read_text().strip().splitlines()
    assert len(manifest_content) == 3, "Expected three checksum entries"
    for line in manifest_content:
        parts = line.split(",")
        assert len(parts) == 3, "Each checksum line must have three comma‑separated fields"
