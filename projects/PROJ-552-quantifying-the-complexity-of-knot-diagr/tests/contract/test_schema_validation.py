"""Contract test for the knot record schema.

Validates that the data produced by the parser conforms to the
schema defined in contracts/knot_record.schema.yaml.
"""
import csv
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import validate, ValidationError

# Path constants
SCHEMA_PATH = Path("contracts/knot_record.schema.yaml")
DATA_PATH = Path("data/processed/knots_cleaned.csv")


@pytest.fixture
def schema():
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def records():
    """Load records from the cleaned CSV file."""
    if not DATA_PATH.exists():
        pytest.fail(f"Data file not found: {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_schema_validation(schema, records):
    """Validate each record in the CSV against the schema."""
    if not records:
        pytest.fail("No records found in the CSV file to validate.")

    for i, record in enumerate(records):
        # Convert numeric strings to appropriate types for validation
        processed_record = {}
        for key, value in record.items():
            if value == "":
                processed_record[key] = None
            elif key in ("crossing_number", "braid_index", "arc_index", "seifert_circle_count", "bridge_number"):
                try:
                    processed_record[key] = int(value)
                except ValueError:
                    processed_record[key] = None
            elif key == "volume":
                try:
                    processed_record[key] = float(value)
                except ValueError:
                    processed_record[key] = None
            elif key == "alternating":
                processed_record[key] = value.lower() == "true" if value else None
            else:
                processed_record[key] = value

        try:
            validate(instance=processed_record, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Record {i} failed validation: {e.message}")
