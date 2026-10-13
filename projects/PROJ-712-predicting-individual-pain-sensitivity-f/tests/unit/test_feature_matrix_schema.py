"""
Unit test for validating the feature matrix CSV against the JSON schema.
The schema lives in ``contracts/dataset.schema.yaml`` and defines
required columns, types, and constraints for the processed feature matrix.
"""
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

# Import the expected column ordering from the central config
from config import EXPECTED_FEATURE_COLUMNS

def _load_schema():
    schema_path = Path(__file__).resolve().parents[3] / "contracts" / "dataset.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def feature_matrix_path(tmp_path):
    """
    Create a minimal but valid feature matrix CSV that complies with the
    schema. The CSV contains a single participant row with dummy values.
    """
    df = pd.DataFrame(
        [
            {
                "participant_id": "sub-001",
                "heat_pain_threshold": "45.0",
                "age": "30",
                "gender": "F",
                "valid_eeg_minutes": "5.0",
                **{col: 0.1 for col in EXPECTED_FEATURE_COLUMNS},
            }
        ]
    )
    csv_path = tmp_path / "feature_matrix.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_feature_matrix_schema_validation(feature_matrix_path):
    """
    Load the CSV, convert each row to a JSON‑compatible dict, and validate
    against the JSON schema. The test fails if any validation error occurs.
    """
    schema = _load_schema()
    df = pd.read_csv(feature_matrix_path, dtype=str)

    # Convert each row to a dict (JSON object) for validation
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        # jsonschema expects proper types; we let it coerce where appropriate
        try:
            jsonschema.validate(instance=row_dict, schema=schema)
        except jsonschema.ValidationError as exc:
            pytest.fail(f"Schema validation error: {exc.message}")