"""
Test for T002 – verifies that each downloaded dataset's metadata is correct,
the CSV file exists, its SHA-256 checksum matches the recorded value, and the
number of samples used does not exceed the 5,000 cap.
"""

import json
import hashlib
from pathlib import Path

import pandas as pd
import pytest

from download import DATASETS, DATA_RAW_DIR, CHECKSUM_MANIFEST

@pytest.fixture(scope="module")
def metadata_files():
    """Collect all metadata JSON files produced by ``download_all``."""
    # Ensure the download step has been executed before tests run.
    from download import download_all
    download_all()

    meta_paths = []
    for dataset_id in DATASETS.keys():
        meta_path = DATA_RAW_DIR / f"{dataset_id}_metadata.json"
        assert meta_path.is_file(), f"Metadata file missing: {meta_path}"
        meta_paths.append(meta_path)
    return meta_paths

def compute_sha256(filepath: Path) -> str:
    """Utility to compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def test_metadata_and_checksum(metadata_files):
    """Validate each metadata JSON against the specification."""
    for meta_path in metadata_files:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # Required keys
        required_keys = {
            "dataset_id",
            "source_url",
            "n_samples_original",
            "n_samples_used",
            "checksum",
        }
        assert required_keys.issubset(meta.keys()), f"Missing keys in {meta_path}"

        dataset_id = meta["dataset_id"]
        csv_path = DATA_RAW_DIR / DATASETS[dataset_id]["filename"]
        assert csv_path.is_file(), f"CSV file missing for dataset {dataset_id}"

        # Verify checksum matches the file content
        actual_checksum = compute_sha256(csv_path)
        assert actual_checksum == meta["checksum"], (
            f"Checksum mismatch for {dataset_id}: "
            f"{actual_checksum} != {meta['checksum']}"
        )

        # Verify cap constraint
        used = int(meta["n_samples_used"])
        assert used <= 5000, f"Dataset {dataset_id} exceeds cap: {used} rows"

        # Load the raw CSV (which is already capped on disk) and compare shape to n_samples_used
        df = pd.read_csv(csv_path)
        assert len(df) == used, (
            f"Row count mismatch for {dataset_id}: "
            f"CSV has {len(df)} rows, metadata reports {used}"
        )

        # Verify required columns exist
        assert "composition" in df.columns, f"'composition' column missing in {dataset_id}"
        # Find a numeric target column (any column other than composition that is numeric)
        numeric_cols = [c for c in df.select_dtypes(include='number').columns if c != "composition"]
        assert numeric_cols, f"No numeric target column found in {dataset_id}"
        # Ensure at least 100 non-null values in the target column
        target_col = numeric_cols[0]
        non_null_count = df[target_col].notna().sum()
        assert non_null_count >= 100, (
            f"Target column '{target_col}' in {dataset_id} has only {non_null_count} non-null rows"
        )

def test_checksum_manifest():
    """Ensure the manifest contains a line for each dataset with matching checksum."""
    manifest_path = CHECKSUM_MANIFEST
    assert manifest_path.is_file(), "Checksum manifest file missing"

    # Load manifest lines
    manifest_entries = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            dataset_id, filename, checksum = line.split(",", 2)
            manifest_entries[dataset_id] = (filename, checksum)

    # Verify each dataset appears exactly once and checksum matches metadata
    for dataset_id, cfg in DATASETS.items():
        assert dataset_id in manifest_entries, f"{dataset_id} missing from manifest"
        filename, checksum = manifest_entries[dataset_id]
        expected_filename = cfg["filename"]
        assert filename == expected_filename, (
            f"Filename mismatch in manifest for {dataset_id}: "
            f"{filename} != {expected_filename}"
        )
        # Load metadata to compare checksum
        meta_path = DATA_RAW_DIR / f"{dataset_id}_metadata.json"
        with open(meta_path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)
        assert checksum == meta["checksum"], (
            f"Checksum in manifest does not match metadata for {dataset_id}"
        )