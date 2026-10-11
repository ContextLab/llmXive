"""
Integration test for ``code/data/curate_reference_substructures.py``.

The test runs the script's ``main`` function and checks that:
  1. ``data/raw/reference_substructures_raw.csv`` exists.
  2. The CSV contains the required columns.
  3. ``data/raw/checksums.json`` contains a ``reference_substructures`` entry
     whose ``hash`` matches the actual SHA‑256 of the copied file.
"""

import json
import hashlib
from pathlib import Path

import pytest

# Import the script's entry point
from code.data.curate_reference_substructures import main as curate_main

@pytest.fixture(scope="module")
def raw_csv_path():
    """Path to the curated reference substructures CSV."""
    return Path(__file__).parents[2] / "data" / "raw" / "reference_substructures_raw.csv"

@pytest.fixture(scope="module")
def checksums_path():
    """Path to the checksums manifest."""
    return Path(__file__).parents[2] / "data" / "raw" / "checksums.json"

def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_curate_reference_substructures(raw_csv_path: Path, checksums_path: Path):
    # Ensure a clean state before running the script
    if raw_csv_path.exists():
        raw_csv_path.unlink()
    if checksums_path.is_file():
        checksums_path.unlink()

    # Run the curation script
    curate_main()

    # 1. The raw CSV must exist
    assert raw_csv_path.is_file(), f"{raw_csv_path} was not created."

    # 2. CSV must contain required columns (case‑insensitive)
    import pandas as pd
    df = pd.read_csv(raw_csv_path)
    cols = set(c.strip().lower() for c in df.columns)
    required = {"smiles", "source_doi", "description"}
    assert required.issubset(cols), f"Missing columns in CSV: {required - cols}"

    # 3. Checksums manifest must contain a matching entry
    assert checksums_path.is_file(), "checksums.json was not created."
    with checksums_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "reference_substructures" in manifest, "Missing manifest entry for reference_substructures."
    entry = manifest["reference_substructures"]
    expected_hash = calculate_sha256(raw_csv_path)
    assert entry["hash"] == expected_hash, "Checksum in manifest does not match actual file hash."