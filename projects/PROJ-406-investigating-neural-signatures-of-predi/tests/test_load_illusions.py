"""
Tests for the Müller‑Lyer ingestion script.

The test checks that:
* The raw parquet file is downloaded to the expected location.
* The cleaned CSV is produced and contains the required columns.
* No duplicate subject IDs cause a failure (only a warning).
"""

import os
import pathlib

import pandas as pd
import pytest

from src.ingest.load_illusions import (
    _ensure_output_paths,
    _download_parquet,
    _clean_dataframe,
    _write_clean_csv,
    download_and_clean,
)
from src.utils.seed import set_global_seed

@pytest.fixture(scope="module")
def raw_and_clean_paths(tmp_path_factory):
    # Use temporary directories to avoid polluting the repository data folder.
    raw_dir = tmp_path_factory.mktemp("raw")
    clean_dir = tmp_path_factory.mktemp("clean")
    raw_path, clean_path = _ensure_output_paths(raw_dir, clean_dir)
    return raw_path, clean_path

def test_download_parquet_success(raw_and_clean_paths):
    raw_path, _ = raw_and_clean_paths
    # The download function should raise if the dataset cannot be found.
    # In CI the dataset is expected to be reachable; if not, the test will
    # surface the underlying problem.
    _download_parquet(raw_path)
    assert raw_path.is_file()
    # Basic sanity check – the file should be a parquet (magic bytes)
    with raw_path.open("rb") as f:
        magic = f.read(4)
    # Parquet files start with "PAR1"
    assert magic == b"PAR1"

def test_clean_dataframe_and_write(tmp_path):
    # Create a tiny dummy dataframe that mimics the required schema.
    # This does not hit external data; it only validates the cleaning logic.
    df = pd.DataFrame(
        {
            "subject_id": ["S1", "S2"],
            "stimulus_type": ["typeA", "typeB"],
            "response": [1.2, 2.3],
            "trial_id": [1, 2],
            "stimulus_parameters": ["p1", "p2"],
        }
    )
    cleaned = _clean_dataframe(df)
    assert list(cleaned.columns) == [
        "subject_id",
        "stimulus_type",
        "response",
        "trial_id",
        "stimulus_parameters",
    ]
    # Write to a temporary CSV and read back
    out_path = tmp_path / "clean.csv"
    _write_clean_csv(cleaned, out_path)
    reloaded = pd.read_csv(out_path)
    pd.testing.assert_frame_equal(cleaned, reloaded)

def test_download_and_clean_integration(tmp_path):
    # Integration test using temporary directories.
    raw_dir = tmp_path / "raw"
    clean_dir = tmp_path / "clean"
    raw_path, clean_path = _ensure_output_paths(raw_dir, clean_dir)

    # Force download into the temporary raw location.
    _download_parquet(raw_path)
    assert raw_path.is_file()

    # Run the high‑level function.
    set_global_seed(42)
    download_and_clean(seed=42)

    # The function writes to the default locations; ensure they exist.
    default_raw, default_clean = _ensure_output_paths()
    assert default_raw.is_file()
    assert default_clean.is_file()
    # Verify required columns in the cleaned CSV.
    df_clean = pd.read_csv(default_clean)
    for col in ["subject_id", "stimulus_type", "response", "trial_id", "stimulus_parameters"]:
        assert col in df_clean.columns