"""
Unit tests for the ingestion pipeline (task T002).

The test builds a tiny synthetic CSV with the required schema columns,
invokes :func:`run_ingest` with ``raw_csv_paths`` pointing at the synthetic file,
and checks that:
  1. The ``checksum`` column exists.
  2. All stress values have been converted to MPa (i.e. are ≤ 1000).
  3. Rows where ``residual_stress_measured`` was missing are flagged with
     ``is_proxy=True`` and have a non‑null ``residual_stress_proxy``.
  4. The output CSV validates against the JSON‑Schema contract.
The synthetic data is only used for the test suite; it is not part of the
scientific analysis.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.ingest.ingest import run_ingest, _validate_schema

# Path to the JSON‑Schema used for validation
SCHEMA_PATH = Path(
    "specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml"
)

@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    """Create a 10‑row CSV matching the required schema."""
    rows = []
    for i in range(10):
        row = {
            "sample_id": f"id_{i}",
            "material_class": "steel" if i % 2 == 0 else "aluminum",
            "heat_input": 5.0 + i,          # MJ
            "cooling_rate": 0.5 + 0.1 * i,  # K/s
            "other_process_params": json.dumps({"param": i}),
            "elastic_modulus": 200.0,
            "yield_strength": 250.0,
            "fatigue_life_cycles": 10000 + i * 100,
            "source": "synthetic",
        }
        # Introduce missing measured stress on odd rows
        if i % 2 == 0:
            row["residual_stress_measured"] = 300.0  # MPa (already in MPa)
        else:
            row["residual_stress_measured"] = pd.NA
        rows.append(row)

    df = pd.DataFrame(rows)
    csv_path = tmp_path / "synthetic.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_run_ingest_creates_unified_csv(synthetic_csv: Path, tmp_path: Path):
    """Run the ingestion on the synthetic CSV and validate the output."""
    output_path = tmp_path / "unified_fatigue.csv"
    # Execute ingestion using the synthetic file as the sole input
    result_df = run_ingest(
        output_path=output_path,
        raw_csv_paths=[synthetic_csv],
        limit_rows=None,
    )

    # 1. checksum column exists
    assert "checksum" in result_df.columns

    # 2. stress values are in MPa (<= 1000) – proxy values are also clamped
    stress_vals = pd.to_numeric(result_df["residual_stress_measured"], errors="coerce")
    assert stress_vals.max() <= 1000

    # 3. proxy rows are flagged correctly
    proxy_mask = result_df["is_proxy"]
    assert proxy_mask.sum() == 5  # half of the rows lacked measured stress
    # proxy column should be non‑null where proxy is True
    assert result_df.loc[proxy_mask, "residual_stress_proxy"].notna().all()

    # 4. schema validation passes (will raise if invalid)
    _validate_schema(result_df, SCHEMA_PATH)

    # Ensure the file was written to disk
    assert output_path.is_file()
