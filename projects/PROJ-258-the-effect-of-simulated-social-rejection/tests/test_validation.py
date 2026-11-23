"""
Unit tests for the validation script (code/validate.py).

The tests use a small in‑memory parquet file created on the fly to avoid
network access.  They verify that:

* A correctly formatted dataset yields a JSON report with ``status:
  "pass"``.
* Missing required columns cause a failure and the script exits with a
  non‑zero status.
* Absence of the required condition values also triggers a failure.
"""

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the validation entry‑point directly
from validate import validate_dataset, main

@pytest.fixture
def minimal_dataset(tmp_path: Path):
    """Create a minimal valid dataset and write it as parquet."""
    df = pd.DataFrame({
        "participant_id": [1, 2, 3],
        "condition": ["rejection", "control", "rejection"],
        "reaction_time": [0.5, 0.7, 0.6],
        "mood_rating": [5, 6, 7],
    })
    parquet_path = tmp_path / "valid.parquet"
    df.to_parquet(parquet_path, index=False)
    return parquet_path

def test_validate_success(minimal_dataset: Path, tmp_path: Path):
    report = validate_dataset(minimal_dataset)
    assert report["status"] == "pass"
    assert "participant_id" in report["columns_present"]
    assert "condition" in report["columns_present"]
    assert "reaction_time" in report["columns_present"]
    assert "mood_rating" in report["columns_present"]

def test_missing_column(minimal_dataset: Path):
    # Load, drop a required column, write back
    df = pd.read_parquet(minimal_dataset)
    df = df.drop(columns=["reaction_time"])
    broken_path = minimal_dataset.parent / "missing_col.parquet"
    df.to_parquet(broken_path, index=False)

    with pytest.raises(ValueError) as excinfo:
        validate_dataset(broken_path)
    assert "reaction_time" in str(excinfo.value).lower()

def test_missing_condition_value(minimal_dataset: Path):
    # Replace 'control' with something else
    df = pd.read_parquet(minimal_dataset)
    df.loc[df["condition"] == "control", "condition"] = "other"
    broken_path = minimal_dataset.parent / "missing_condition.parquet"
    df.to_parquet(broken_path, index=False)

    with pytest.raises(ValueError) as excinfo:
        validate_dataset(broken_path)
    assert "control" in str(excinfo.value).lower()

def test_main_integration(tmp_path: Path):
    """
    End‑to‑end test: place a valid parquet file in the expected raw
    directory, run ``validate.main()`` and check that the JSON report
    appears with status pass.
    """
    # Mimic project layout
    raw_dir = tmp_path / "data" / "raw"
    interim_dir = tmp_path / "data" / "interim"
    raw_dir.mkdir(parents=True)
    interim_dir.mkdir(parents=True)

    # Write a valid parquet file
    df = pd.DataFrame({
        "participant_id": [1],
        "condition": ["rejection"],
        "reaction_time": [0.5],
        "mood_rating": [5],
    })
    parquet_path = raw_dir / "ds000208.parquet"
    df.to_parquet(parquet_path, index=False)

    # Patch ``config.get_path`` to point to our temporary dirs
    import importlib
    import config as cfg

    original_get_path = cfg.get_path

    def fake_get_path(key: str):
        if key == "raw":
            return str(raw_dir)
        if key == "interim":
            return str(interim_dir)
        return original_get_path(key)

    cfg.get_path = fake_get_path

    # Run validation
    try:
        main()
    finally:
        # Restore original function to avoid side effects on other tests
        cfg.get_path = original_get_path

    # Verify report exists
    report_path = interim_dir / "ingest_validation_ds000208.json"
    assert report_path.is_file()
    with open(report_path) as f:
        report = json.load(f)
    assert report["status"] == "pass"

# Ensure the script exits with the appropriate code when failures occur
def test_main_exits_on_failure(tmp_path: Path):
    raw_dir = tmp_path / "data" / "raw"
    interim_dir = tmp_path / "data" / "interim"
    raw_dir.mkdir(parents=True)
    interim_dir.mkdir(parents=True)

    # Create a broken parquet (missing required column)
    df = pd.DataFrame({
        "participant_id": [1],
        "condition": ["rejection"],
        "mood_rating": [5],
    })
    parquet_path = raw_dir / "bad.parquet"
    df.to_parquet(parquet_path, index=False)

    import config as cfg

    original_get_path = cfg.get_path

    def fake_get_path(key: str):
        if key == "raw":
            return str(raw_dir)
        if key == "interim":
            return str(interim_dir)
        return original_get_path(key)

    cfg.get_path = fake_get_path

    # Capture sys.exit
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1

    cfg.get_path = original_get_path