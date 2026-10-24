"""
test_simulated_schema.py

Ensures that the simulated measurement records conform to the
``MeasurementRecord`` schema defined in ``contracts/dataset.schema.yaml``.
"""
from pathlib import Path

import pytest

# Import the validation helper from the script we just created.
from code.validation.validate_schema import validate_csv_against_schema


@pytest.mark.parametrize(
    "schema_path,data_path",
    [
        (
            Path("contracts/dataset.schema.yaml"),
            Path("data/raw/measurement_records_sim.csv"),
        )
    ],
)
def test_simulated_measurement_records_valid(schema_path: Path, data_path: Path):
    """
    The function should complete without raising a ``jsonschema.ValidationError``.
    If the CSV violates the schema the test will fail, highlighting the exact
    issue.
    """
    # The helper raises on validation failure; a successful call means the
    # simulated data is schema‑compliant.
    validate_csv_against_schema(schema_path, data_path)