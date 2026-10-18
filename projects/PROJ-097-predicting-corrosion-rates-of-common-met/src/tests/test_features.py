"""Tests for the feature‑engineering module (T003).

The test runs the ``features`` entry point and verifies that the expected
output files are created and contain the required interaction columns.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths, get_logger
from src.pipeline.features import main as features_main

log = get_logger(__name__)

@pytest.fixture(scope="module")
def run_features():
    """Execute the feature‑engineering script once for the test session."""
    exit_code = features_main([])
    assert exit_code == 0, "features script exited with non‑zero code"
    yield

def test_features_parquet_created(run_features):
    """Assert that the Parquet file exists and contains engineered columns."""
    parquet_path = paths.data("processed", "features.parquet")
    assert parquet_path.is_file(), f"Missing {parquet_path}"
    df = pd.read_parquet(parquet_path)

    # Expected interaction columns (examples).
    expected_cols = [
        "ph_x_salinity",
        "ph_x_temperature",
        "salinity_x_temperature",
    ]
    for col in expected_cols:
        assert col in df.columns, f"Interaction column {col} not found"

    # Verify residualization: interaction columns should have near‑zero
    # covariance with each of their main‑effect columns.
    for col in expected_cols:
        parts = col.split("_x_")
        if len(parts) != 2:
            continue
        main1, main2 = parts
        cov1 = df[col].cov(df[main1])
        cov2 = df[col].cov(df[main2])
        assert abs(cov1) < 1e-6, f"Covariance {cov1:.2e} between {col} and {main1} not near zero"
        assert abs(cov2) < 1e-6, f"Covariance {cov2:.2e} between {col} and {main2} not near zero"

def test_feature_names_json(run_features):
    """Check that the feature‑name JSON file lists all non‑target columns."""
    names_path = paths.data("processed", "feature_names.json")
    assert names_path.is_file(), f"Missing {names_path}"
    with open(names_path, "r", encoding="utf-8") as fh:
        names = json.load(fh)
    assert isinstance(names, list) and names, "Feature name list is empty or not a list"

    # Ensure that at least one engineered interaction appears in the list.
    assert any("_x_" in n for n in names), "No interaction feature names recorded"
