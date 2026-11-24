"""Tests for T006 data ingestion output."""

import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = PROJECT_ROOT / "data" / "raw" / "merged_dataset.parquet"
METRICS_PATH = PROJECT_ROOT / "artifacts" / "reports" / "metrics.json"

PHENOTYPE_COLUMNS = ["species", "root_length", "branching_density", "surface_area"]
NUTRIENT_COLUMNS = ["phosphorus", "nitrogen"]


@pytest.mark.skipif(
    not PARQUET_PATH.exists(), reason="merged_dataset.parquet not generated yet"
)
def test_output_contains_phenotype_and_nutrient_columns():
    df = pd.read_parquet(PARQUET_PATH)
    for col in PHENOTYPE_COLUMNS + NUTRIENT_COLUMNS:
        assert col in df.columns, f"missing column: {col}"
    assert len(df) > 0


@pytest.mark.skipif(
    not METRICS_PATH.exists(), reason="metrics.json not generated yet"
)
def test_metrics_contain_merge_success_rate():
    with open(METRICS_PATH) as f:
        metrics = json.load(f)
    assert "merge_success_rate" in metrics
    rate = metrics["merge_success_rate"]
    assert isinstance(rate, float)
    assert 0.0 <= rate <= 1.0


def test_merge_nearest_soil_respects_radius():
    """Nearest‑neighbour matching must not attach soil beyond 10 km."""
    from ingestion import compute_merge_success_rate, merge_nearest_soil

    root = pd.DataFrame(
        {
            "species": ["a", "b"],
            "root_length": [1.0, 2.0],
            "latitude": [10.0, 10.0],
            "longitude": [10.0, 10.0],
        }
    )
    soil = pd.DataFrame(
        {
            "latitude": [10.001, 20.0],  # ~0.11 km and ~1100 km away
            "longitude": [10.0, 10.0],
            "phosphorus": [5.0, 99.0],
            "nitrogen": [2.0, 88.0],
        }
    )
    merged = merge_nearest_soil(root, soil)
    assert merged.loc[0, "phosphorus"] == 5.0
    assert pd.isna(merged.loc[1, "phosphorus"])
    assert compute_merge_success_rate(merged) == 0.5