"""
test_features.py
----------------
Basic sanity checks for the feature‑set builder.

The test suite creates a tiny synthetic ``unified_fatigue.csv`` with the
minimal columns required by the builder, invokes :func:`build_feature_sets`,
and then verifies the relationships between the produced sets.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from code.src.build_features import build_feature_sets

# Path to the JSON‑Schema (required only for ingestion – not used here)
SCHEMA_PATH = Path(
    "specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml"
)

@pytest.fixture
def synthetic_unified(tmp_path: Path) -> Path:
    """Create a minimal unified CSV matching the expected schema."""
    rows = []
    for i in range(8):
        rows.append({
            "sample_id": f"id_{i}",
            "material_class": "steel" if i % 2 == 0 else "aluminum",
            "heat_input": 5.0 + i,
            "cooling_rate": 0.5 + 0.1 * i,
            "other_process_params": json.dumps({"p": i}),
            "elastic_modulus": 200.0,
            "yield_strength": 250.0,
            "fatigue_life_cycles": 10000 + i * 100,
            "residual_stress_measured": 300.0 if i % 2 == 0 else pd.NA,
            "residual_stress_proxy": 300.0 if i % 2 == 0 else 0.05,
            "is_proxy": i % 2 == 1,
        })
    df = pd.DataFrame(rows)
    out_path = tmp_path / "unified_fatigue.csv"
    df.to_csv(out_path, index=False)
    return out_path

def test_feature_sets_build_correctly(synthetic_unified: Path, tmp_path: Path):
    """
    Verify that:
    1. Feature Set A and the balanced B set share the same row count
       (balanced subset) and the same indices after construction.
    2. Balanced B contains no proxy rows (``is_proxy`` must be False).
    3. B‑full and C span the full dataset and correctly use the proxy column.
    """
    # Build the sets using the synthetic unified file.
    feature_dict = build_feature_sets(unified_path=synthetic_unified)

    # ---- 1. A vs B_balanced indices ----
    assert len(feature_dict["A"]) == len(feature_dict["B_balanced"])
    # The rows in B_balanced correspond exactly to the rows where is_proxy=False.
    df_unified = pd.read_csv(synthetic_unified)
    measured_mask = ~df_unified["is_proxy"]
    assert len(measured_mask) == len(feature_dict["B_balanced"])

    # ---- 2. No proxy rows in balanced B ----
    # The balanced set should not contain the ``is_proxy`` flag at all;
    # we only included the measured stress column.
    assert "is_proxy" not in feature_dict["B_balanced"].columns
    # Ensure the stress column has no missing values.
    assert feature_dict["B_balanced"]["residual_stress_measured"].notna().all()

    # ---- 3. B_full and C cover the full dataset ----
    assert len(feature_dict["B_full"]) == len(df_unified)
    assert len(feature_dict["C"]) == len(df_unified)

    # In B_full the ``residual_stress`` column must be present.
    assert "residual_stress" in feature_dict["B_full"].columns

    # In C the proxy column must be present and non‑null for every row.
    assert "residual_stress_proxy" in feature_dict["C"].columns
    assert feature_dict["C"]["residual_stress_proxy"].notna().all()