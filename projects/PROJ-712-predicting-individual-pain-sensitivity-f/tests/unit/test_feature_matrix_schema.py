"""
Unit test that validates the generated feature matrix CSV against the
JSON‑schema defined in ``contracts/dataset.schema.yaml``.
"""
import json
import pathlib

import pandas as pd
import pytest
import yaml
from jsonschema import validate, ValidationError

# Path to the CSV produced by the preprocessing step
FEATURE_CSV = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed" / "feature_matrix.csv"

# Path to the JSON‑schema contract
SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[3] / "contracts" / "dataset.schema.yaml"

@pytest.mark.integration
def test_feature_matrix_schema():
    # Ensure the CSV exists
    assert FEATURE_CSV.is_file(), f"Feature matrix not found at {FEATURE_CSV}"

    # Load CSV into a list of dicts (JSON‑compatible)
    df = pd.read_csv(FEATURE_CSV, dtype=str)
    records = df.to_dict(orient="records")

    # Load JSON schema
    with open(SCHEMA_PATH, "r") as f:
        schema = yaml.safe_load(f)

    # Validate each record against the schema
    for i, rec in enumerate(records):
        try:
            validate(instance=rec, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Record {i} failed schema validation: {e.message}")