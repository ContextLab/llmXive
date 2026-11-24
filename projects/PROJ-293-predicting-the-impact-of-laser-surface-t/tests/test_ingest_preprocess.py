"""
Tests for the preprocessing functions introduced in Task T003.

The test suite validates:
  * No NaN values remain in the required predictor columns after
    `handle_missing_values` (i.e., `aggregated_dropped.csv`).
  * Normalized rows contain a non‑null `wear_coefficient_K` column
    (i.e., `aggregated_clean.csv`).
  * The split summary JSON counts match the lengths of the generated CSVs
    and that train / test splits are disjoint.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def merged_path():
    return paths.data("intermediate", "merged.csv")

@pytest.fixture(scope="module")
def dropped_path():
    return paths.data("processed", "aggregated_dropped.csv")

@pytest.fixture(scope="module")
def clean_path():
    return paths.data("processed", "aggregated_clean.csv")

@pytest.fixture(scope="module")
def normalized_path():
    return paths.data("processed", "normalized_only.csv")

@pytest.fixture(scope="module")
def raw_path():
    return paths.data("processed", "raw_only.csv")

@pytest.fixture(scope="module")
def split_summary_path():
    return paths.data("processed", "split_summary.json")

@pytest.fixture(scope="module")
def train_split_path():
    return paths.data("processed", "train_split.csv")

@pytest.fixture(scope="module")
def test_split_path():
    return paths.data("processed", "test_split.csv")

def test_missing_predictor_handling(dropped_path):
    """Aggregated_dropped.csv must have no NaNs in required predictors."""
    df = pd.read_csv(dropped_path)
    required = [
        "pulse_duration",
        "power",
        "scanning_speed",
        "pattern_geometry",
        "hardness",
        "elastic_modulus",
    ]
    # Verify required columns exist
    for col in required:
        assert col in df.columns, f"Missing required column {col}"
    # Ensure no NaNs in those columns
    assert not df[required].isnull().any().any(), "NaNs found in required predictors"

def test_archard(clean_path):
    """Aggregated_clean.csv must contain a non‑null K for normalized rows."""
    df = pd.read_csv(clean_path)
    assert "normalization_method" in df.columns, "Missing normalization_method column"
    normalized = df[df["normalization_method"] == "normalized"]
    # Normalized rows must have a wear_coefficient_K column with no NaNs
    assert "wear_coefficient_K" in normalized.columns, "Missing wear_coefficient_K column"
    assert not normalized["wear_coefficient_K"].isnull().any(), "NaNs in wear_coefficient_K for normalized rows"

def test_split(split_summary_path, normalized_path, raw_path, train_split_path, test_split_path):
    """Check that summary counts match CSV lengths and splits are disjoint."""
    with split_summary_path.open() as f:
        summary = json.load(f)

    normalized_df = pd.read_csv(normalized_path)
    raw_df = pd.read_csv(raw_path)
    train_df = pd.read_csv(train_split_path)
    test_df = pd.read_csv(test_split_path)

    assert summary["total_count"] == len(train_df) + len(test_df), "Total count mismatch"
    assert summary["normalized_count"] == len(normalized_df), "Normalized count mismatch"
    assert summary["raw_count"] == len(raw_df), "Raw count mismatch"

    # Ensure train and test indices are disjoint
    train_ids = set(train_df.index)
    test_ids = set(test_df.index)
    assert train_ids.isdisjoint(test_ids), "Train and test splits overlap"