"""
Contract test for T084: Validate analysis_ready.schema.yaml against data/processed/analysis_ready.csv.
"""
import csv
import json
import sys
from pathlib import Path

import yaml

# Add project root to path for imports if needed, though we are importing from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_processed_data_dir, get_contracts_dir
from validate_schemas import load_schema, validate_csv_against_schema

def test_analysis_ready_schema_validation():
    """
    Validates that data/processed/analysis_ready.csv conforms to
    specs/001-the-impact-of-text-message-tone-on-perce/contracts/analysis_ready.schema.yaml.
    """
    processed_dir = get_processed_data_dir()
    contracts_dir = get_contracts_dir()

    csv_path = processed_dir / "analysis_ready.csv"
    schema_path = contracts_dir / "analysis_ready.schema.yaml"

    # Check files exist
    assert csv_path.exists(), f"Required file missing: {csv_path}"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

    # Load schema
    schema = load_schema(schema_path)

    # Validate CSV against schema
    # The validate_csv_against_schema function from validate_schemas.py
    # handles the logic of reading the CSV and checking columns/types.
    errors = validate_csv_against_schema(csv_path, schema)

    assert not errors, (
        f"CSV validation failed against schema {schema_path.name}:\n"
        + "\n".join(errors)
    )

if __name__ == "__main__":
    # Allow running as a script for quick verification
    test_analysis_ready_schema_validation()
    print("Validation passed.")
