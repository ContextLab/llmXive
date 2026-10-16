"""
Unit test for the performance‑metrics CSV generation (Task T002).

The test creates a tiny synthetic raw‑JSON dataset (which is permissible
for a unit‑test – it does not constitute the research data) and runs the
CSV generator.  It then validates:
  * the CSV file exists,
  * it contains at least one data row,
  * no NaN/Inf values are present,
  * each row conforms to the JSON schema defined at
    specs/001-exploring-the-role-of-network-structure/contracts/performance_metrics.schema.yaml.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
from jsonschema import Draft7Validator

# Import the generator from the existing module
from generate_calibration_csv import generate_performance_csv


@pytest.fixture
def synthetic_raw_dir(tmp_path: Path) -> Path:
    """
    Create a temporary ``data/raw``‑style directory with two well‑formed
    JSON snapshots.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Helper to build a minimal calibration dict
    def make_snapshot(device_id: str, timestamp: str) -> dict:
        # Two qubits, each with T1/T2 values
        qubits = [
            [
                {"name": "T1", "value": 100.0},
                {"name": "T2", "value": 80.0},
            ],
            [
                {"name": "T1", "value": 120.0},
                {"name": "T2", "value": 90.0},
            ],
        ]
        # One CX gate with error and readout error parameters
        gates = [
            {
                "gate": "cx",
                "parameters": [
                    {"name": "gate_error", "value": 0.02},
                    {"name": "readout_error", "value": 0.03},
                ],
            }
        ]
        return {
            "device_id": device_id,
            "timestamp": timestamp,
            "qubits": qubits,
            "gates": gates,
        }

    # Create two snapshots
    snap1 = make_snapshot("ibmq_test1", "2024-09-01T12:00:00Z")
    snap2 = make_snapshot("ibmq_test2", "2024-09-01T13:00:00Z")

    (raw_dir / "snap1.json").write_text(json.dumps(snap1), encoding="utf-8")
    (raw_dir / "snap2.json").write_text(json.dumps(snap2), encoding="utf-8")

    return raw_dir


@pytest.fixture
def schema_validator() -> Draft7Validator:
    """Load the JSON schema for performance metrics."""
    schema_path = Path(
        "specs/001-exploring-the-role-of-network-structure/contracts/performance_metrics.schema.yaml"
    )
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return Draft7Validator(schema)


def test_generate_performance_csv_creates_valid_file(
    synthetic_raw_dir: Path, tmp_path: Path, schema_validator: Draft7Validator
):
    """
    Run the CSV generator on the synthetic raw directory and validate the output.
    """
    output_csv = tmp_path / "performance_metrics.csv"

    # Execute the generator (this is the code under test)
    generate_performance_csv(raw_dir=synthetic_raw_dir, output_path=output_csv)

    # 1. File existence
    assert output_csv.is_file(), f"CSV not created at {output_csv}"

    # 2. Load CSV and basic sanity checks
    df = pd.read_csv(output_csv)
    assert not df.empty, "Generated CSV is empty"
    # Ensure expected columns are present
    expected_cols = {
        "device_id",
        "timestamp",
        "t1_mean",
        "t2_mean",
        "cx_error_mean",
        "readout_error_mean",
        "chip_family",
    }
    assert set(df.columns) == expected_cols, "CSV columns mismatch"

    # 3. No NaN/Inf values
    assert not df.isna().any().any(), "CSV contains NaN values"
    assert not df.select_dtypes(include=["float"]).applymap(
        lambda x: pd.isna(x) or pd.isnull(x) or (x == float("inf")) or (x == float("-inf"))
    ).any().any(), "CSV contains infinite values"

    # 4. Schema validation row‑by‑row
    for _, row in df.iterrows():
        # Convert the pandas Series to a plain Python dict with native types
        record = row.to_dict()
        # jsonschema expects native Python types; ensure numbers are floats
        for key in ["t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean"]:
            record[key] = float(record[key])
        # Validate
        schema_validator.validate(record)

# The test suite imports ``yaml`` – ensure it is available in the environment.
# ``PyYAML`` is part of the default runtime, so no extra dependency is needed.
