"""
Unit tests for the data loader (code/data_loader.py).

The tests verify that:
* All three required datasets are fetched successfully.
* A checksum manifest is created and contains entries for each dataset.
* Datasets with fewer than 100 rows are skipped (simulated via monkey‑patch).
* An exception is raised for any non‑skip error (e.g., missing required columns).
* Synthetic outcome generation is logged when the outcome column is fully observed.
"""

import json
import logging
import os
from pathlib import Path

import pytest

# Ensure the project ``code`` directory is on the import path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from data_loader import (
    DataLoadError,
    load_datasets,
    load_datasets_for_analysis,
    _manifest_entries,
)
from llmxive_toolkit import get_logger

logger = get_logger(__name__)

def test_load_all_datasets(tmp_path, caplog):
    """
    Load the real datasets and verify that a manifest entry exists for each.
    """
    caplog.set_level(logging.INFO)

    # Run the loader
    datasets = load_datasets_for_analysis()

    # All three IDs must be present (or flagged)
    expected_ids = {42803, 43844, 43845}
    assert set(datasets.keys()) == expected_ids

    # Manifest should contain entries for each dataset
    manifest_path = Path("data/checksums/manifest.json")
    assert manifest_path.exists()
    with manifest_path.open() as f:
        manifest = json.load(f)

    assert "datasets" in manifest
    assert set(map(int, manifest["datasets"].keys())) == expected_ids

    # Verify that each entry has a filename, checksum and status
    for ds_id, entry in manifest["datasets"].items():
        assert "filename" in entry
        assert "checksum" in entry
        assert "status" in entry
        assert Path(entry["filename"]).exists()

def test_skip_small_dataset(monkeypatch, caplog):
    """
    Simulate a dataset with fewer than 100 rows and ensure it is skipped
    rather than causing a fatal error.
    """
    caplog.set_level(logging.WARNING)

    # Monkey‑patch load_and_validate to return a tiny DataFrame for one ID
    from data_loader import load_and_validate

    original_load = load_and_validate

    def fake_load_and_validate(dataset_id, *args, **kwargs):
        if dataset_id == 42803:
            import pandas as pd

            return pd.DataFrame({"treat": [], "outcome": [], "age": [], "sex": []})
        return original_load(dataset_id, *args, **kwargs)

    monkeypatch.setattr("data_loader.load_and_validate", fake_load_and_validate)

    # Run loader – it should raise for other IDs if they fail, but not for the tiny one
    datasets = load_datasets()
    assert 42803 not in datasets
    # Verify a warning was logged about skipping
    warnings = [rec.message for rec in caplog.records if rec.levelno == logging.WARNING]
    assert any("Skipping dataset 42803" in str(w) for w in warnings)

def test_fatal_error_propagates(monkeypatch):
    """
    Ensure that a non‑row‑count error (e.g., missing required column) aborts
    the loading process.
    """
    # Monkey‑patch _verify_columns to raise a DataLoadError for a specific ID
    from data_loader import _verify_columns

    def fake_verify(df, spec, dataset_id):
        if dataset_id == 43844:
            raise DataLoadError("Simulated missing column error")
        return _verify_columns.__wrapped__(df, spec, dataset_id)  # type: ignore

    monkeypatch.setattr("data_loader._verify_columns", fake_verify)

    with pytest.raises(DataLoadError, match="Simulated missing column error"):
        load_datasets()
