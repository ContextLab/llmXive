"""
Contract test for data schema validation against DiffusionRecord entity.
Validates the fetched data against the YAML schema definition.
"""
import pytest
import yaml
import csv
from pathlib import Path
from typing import Dict, Any, Set

# Paths
TEST_DATA_PATH = Path("data/raw/fetched_diffusion.csv")
SCHEMA_PATH = Path("contracts/diffusion_record.schema.yaml")

def load_schema() -> Dict[str, Any]:
    """Load and parse the YAML schema."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_row(row: Dict[str, str], schema: Dict[str, Any], row_idx: int) -> None:
    """Validate a single row against the schema."""
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    
    # Check required fields
    missing_fields = required - set(row.keys())
    if missing_fields:
        pytest.fail(f"Row {row_idx}: Missing required fields: {missing_fields}")
    
    # Validate types and constraints
    for field, value in row.items():
        if field not in properties:
            # If schema says no additional properties, fail
            if not schema.get("additionalProperties", True):
                pytest.fail(f"Row {row_idx}: Unexpected field '{field}'")
            continue
        
        field_schema = properties[field]
        field_type = field_schema.get("type")
        
        if field_type == "number":
            try:
                float(value)
            except ValueError:
                pytest.fail(f"Row {row_idx}: Field '{field}' expected number, got '{value}'")
        
        elif field_type == "string":
            if not isinstance(value, str):
                pytest.fail(f"Row {row_idx}: Field '{field}' expected string")
            
            # Check enum constraints if present
            if "enum" in field_schema:
                if value not in field_schema["enum"]:
                    pytest.fail(f"Row {row_idx}: Field '{field}' value '{value}' not in allowed values: {field_schema['enum']}")

def test_schema_validation():
    """
    Validates the structure of the fetched diffusion data against the DiffusionRecord schema.
    """
    if not TEST_DATA_PATH.exists():
        pytest.skip("Test data file not found. Run acquisition script first.")
    
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file missing at {SCHEMA_PATH}")

    # Load schema
    schema = load_schema()

    # Load data
    with open(TEST_DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        pytest.fail("No data rows found in test data file.")
    
    # Validate each row
    for i, row in enumerate(rows):
        validate_row(row, schema, i)
    
    print(f"Schema validation passed for {len(rows)} records.")

if __name__ == "__main__":
    test_schema_validation()