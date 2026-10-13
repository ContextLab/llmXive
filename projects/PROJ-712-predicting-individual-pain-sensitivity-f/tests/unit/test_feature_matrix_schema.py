"""
Unit test that validates the generated feature matrix CSV against the
JSON‑Schema defined in ``contracts/dataset.schema.yaml``.
"""
import pytest
from pathlib import Path

from code.validate_feature_matrix import validate_feature_matrix

def test_feature_matrix_schema(tmp_path):
    """
    The test creates a minimal, valid CSV using the expected column names
    and then runs the validator.  Any schema violation raises a
    ``jsonschema.ValidationError`` which fails the test.
    """
    # Build a tiny valid CSV
    csv_path = tmp_path / "feature_matrix.csv"
    # Use the EXPECTED_FEATURE_COLUMNS from the config to build the header
    from config import EXPECTED_FEATURE_COLUMNS

    base_cols = ["participant_id", "heat_pain_threshold", "age", "gender", "valid_eeg_minutes"]
    header = base_cols + EXPECTED_FEATURE_COLUMNS
    # Write a single dummy row with placeholder values
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        f.write(
            "sub-01,45,30,M,5.0," + ",".join(["0.0"] * len(EXPECTED_FEATURE_COLUMNS)) + "\n"
        )

    # This should not raise
    validate_feature_matrix(csv_path)