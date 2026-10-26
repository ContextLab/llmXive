"""
Unit tests for src/models/train.py
----------------------------------

The tests focus on the parts that can be exercised without requiring the full
external data download pipeline:

* ``_extract_coords`` correctly normalises latitude/longitude column names.
* ``create_spatial_clusters`` produces a JSON file with exactly five cluster IDs.
* The ``main`` function returns a zero exit‑code when a minimal synthetic CSV is
  present (the test creates a temporary CSV with the required columns).
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test
from src.models import train

def test_extract_coords_renames_columns():
    df = pd.DataFrame({
        "site_id": ["A", "B"],
        "latitude": [10.0, 20.0],
        "longitude": [30.0, 40.0],
    })
    coords = train._extract_coords(df)
    assert set(coords.columns) == {"site_id", "lat", "lon"}
    assert coords.iloc[0]["lat"] == 10.0
    assert coords.iloc[1]["lon"] == 40.0

def test_create_spatial_clusters_writes_json(tmp_path):
    # Prepare a tiny coordinate table with 5 distinct points
    coords = pd.DataFrame({
        "site_id": [f"S{i}" for i in range(5)],
        "lat": [0, 10, 20, 30, 40],
        "lon": [0, 10, 20, 30, 40],
    })
    # Temporarily patch the output path
    orig_path = train.CLUSTERS_OUTPUT
    train.CLUSTERS_OUTPUT = tmp_path / "spatial_clusters.json"

    mapping = train.create_spatial_clusters(coords, n_clusters=5)
    # Ensure mapping contains 5 entries and values are in 0‑4
    assert len(mapping) == 5
    assert set(mapping.values()) == set(range(5))

    # Verify the JSON file content matches the mapping
    with open(train.CLUSTERS_OUTPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == mapping

    # Restore original constant
    train.CLUSTERS_OUTPUT = orig_path

def test_main_runs_with_minimal_dataset(tmp_path, monkeypatch):
    # Create a minimal CSV that satisfies the expectations of the training script
    csv_path = tmp_path / "environmental_time_series.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "site_id": ["S1"] * 4,
        "date": pd.date_range(start="2018-01-01", periods=4, freq="Y"),
        "lat": [10.0] * 4,
        "lon": [20.0] * 4,
        "phenology_target": [100, 110, 120, 130],
        "some_feature": [0.1, 0.2, 0.3, 0.4],
    })
    df.to_csv(csv_path, index=False)

    # Patch the DATA_PATH constant to point at our temporary file
    monkeypatch.setattr(train, "DATA_PATH", csv_path)

    # Run main – it should finish without raising and return exit‑code 0
    exit_code = train.main()
    assert exit_code == 0

    # Check that the model file was created
    model_path = train.MODEL_OUTPUT
    assert model_path.is_file()

    # Clean up monkey‑patched constants
    monkeypatch.setattr(train, "DATA_PATH", train.DATA_PATH)
