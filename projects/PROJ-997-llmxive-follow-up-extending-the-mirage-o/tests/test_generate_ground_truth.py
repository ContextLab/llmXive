"""
Unit tests for the ground‑truth generation pipeline.

The tests are intentionally lightweight – they verify that the wrapper script
creates the expected artefacts and that the statistics file contains a
p‑value below the default 0.05 threshold.  Running the tests requires the
actual data generation step, which is exercised by the execution request
above.
"""

import json
from pathlib import Path

import pytest

@pytest.fixture(scope="module")
def parquet_path():
    return Path("data/processed/training_sample.parquet")

@pytest.fixture(scope="module")
def stats_path():
    return Path("data/processed/dataset_stats.json")

def test_parquet_exists(parquet_path):
    assert parquet_path.is_file(), f"Parquet file not found at {parquet_path}"

def test_stats_exists(stats_path):
    assert stats_path.is_file(), f"Stats JSON not found at {stats_path}"

def test_stats_significant(stats_path):
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)
    per_level = stats.get("per_level_statistics", {})
    # At least one level must have p < 0.05
    assert any(
        v.get("p_value", 1) < 0.05 for v in per_level.values()
    ), "No quantization level achieved statistical significance"