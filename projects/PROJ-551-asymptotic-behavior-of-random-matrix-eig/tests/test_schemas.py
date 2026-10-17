"""
Schema validation test for all processed data files.

This test is part of Task T001 and is re‑used here to ensure that the
newly‑generated ``mc_results.csv`` and ``convergence_data.json`` conform
to the JSON‑Schema contracts stored under ``contracts/``.
"""

import json
import csv
from pathlib import Path

import yaml
import jsonschema
import pytest

# Helper to load a schema from the contracts directory
def _load_schema(schema_name: str) -> dict:
    schema_path = Path("contracts") / schema_name
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# 1. Validate JSON files against their schemas
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "json_file, schema_file",
    [
        ("data/processed/single_run_results.json", "simulation_run.schema.yaml"),
        ("data/processed/repro_check_1.json", "simulation_run.schema.yaml"),
        ("data/processed/convergence_data.json", "aggregated_threshold.schema.yaml"),
    ],
)
def test_json_schema_validation(json_file, schema_file):
    data_path = Path(json_file)
    assert data_path.is_file(), f"{json_file} not found"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    schema = _load_schema(schema_file)
    jsonschema.validate(instance=data, schema=schema)

# ----------------------------------------------------------------------
# 2. Validate CSV files against their schemas (if a CSV schema is defined)
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "csv_file, schema_file",
    [
        ("data/processed/mc_results.csv", "eigenvalue_result.schema.yaml"),
    ],
)
def test_csv_schema_validation(csv_file, schema_file):
    csv_path = Path(csv_file)
    assert csv_path.is_file(), f"{csv_file} not found"

    # Load the CSV into a list of dicts (header → values)
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows, "CSV file is empty"

    schema = _load_schema(schema_file)
    # The schema is expected to describe a single record; we validate each row.
    for row in rows:
        jsonschema.validate(instance=row, schema=schema)