"""
Tests for the performance‑metrics CSV generation script.

The test suite verifies that:
1. The CSV file is created at the expected location.
2. It contains at least one data row.
3. All numeric columns contain finite values (no NaN/Inf).
4. The file conforms to the JSON schema defined in
   ``specs/001-exploring-the-role-of-network-structure/contracts/performance_metrics.schema.yaml``.
"""

import os
import csv
import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

# Import the function directly from the module under test.
from generate_calibration_csv import generate_performance_csv, main

# Resolve project‑relative paths using the toolkit helpers.
from llmxive_toolkit import paths

@pytest.fixture
def raw_dir(tmp_path):
    """
    Create a temporary ``data/raw`` directory containing a single
    minimal but realistic calibration snapshot.  The snapshot mirrors the
    structure produced by ``fetcher`` (nested under ``properties``).
    """
    raw = tmp_path / "raw"
    raw.mkdir(parents=True)

    # Minimal snapshot – matches the sample provided in the repository.
    snapshot = {
        "device_id": "test_device",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "properties": {
            "qubits": [
                [
                    {"name": "T1", "value": 150e-6},
                    {"name": "T2", "value": 100e-6},
                ],
                [
                    {"name": "T1", "value": 160e-6},
                    {"name": "T2", "value": 110e-6},
                ],
            ],
            "gates": [
                {
                    "gate": "cx",
                    "parameters": [
                        {"name": "gate_error", "value": 0.01},
                        {"name": "readout_error", "value": 0.02},
                    ],
                }
            ],
        },
    }

    with open(raw / "snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f)

    return raw

@pytest.fixture
def output_path(tmp_path):
    """Path where the generated CSV will be written."""
    return tmp_path / "processed" / "performance_metrics.csv"

def test_generate_performance_csv_creates_file(raw_dir, output_path):
    """The script must write a CSV file at the declared location."""
    generate_performance_csv(raw_dir=raw_dir, output_path=output_path)
    assert output_path.is_file(), "CSV file was not created"

def test_csv_contains_data_and_is_finite(raw_dir, output_path):
    """CSV must contain at least one row and all numeric fields must be finite."""
    generate_performance_csv(raw_dir=raw_dir, output_path=output_path)

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0, "CSV is empty"

    # Check that numeric columns are present and finite.
    numeric_fields = [
        "t1_mean",
        "t2_mean",
        "cx_error_mean",
        "readout_error_mean",
    ]
    for row in rows:
        for field in numeric_fields:
            value = float(row[field])
            assert not (value != value or value in (float("inf"), float("-inf"))), \
                f"Non‑finite value in column {field}"

def test_schema_validation(raw_dir, output_path):
    """Validate the generated CSV against the declared JSON schema."""
    # Load the JSON schema from the contracts directory.
    schema_path = (
        Path(__file__).parents[2]
        / "specs"
        / "001-exploring-the-role-of-network-structure"
        / "contracts"
        / "performance_metrics.schema.yaml"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    generate_performance_csv(raw_dir=raw_dir, output_path=output_path)

    # Convert CSV rows to JSON‑like dicts for validation.
    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = [dict(row) for row in reader]

    # Each record should validate against the schema.
    for record in records:
        # Cast numeric fields to appropriate types before validation.
        for key in ["t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean"]:
            if key in record:
                record[key] = float(record[key])
        try:
            validate(instance=record, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")