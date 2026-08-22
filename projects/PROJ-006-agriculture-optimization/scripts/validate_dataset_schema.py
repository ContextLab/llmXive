"""
Script to validate the dataset schema (contracts/dataset.schema.yaml)
using pydantic for structural integrity checks.

This script implements the verification step for T007.
"""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field, ValidationError, field_validator
from datetime import datetime

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

class DatasetSchema(BaseModel):
    """Pydantic model representing the Dataset Schema for validation."""
    type: str
    required: list[str]
    properties: Dict[str, Any]
    additionalProperties: bool

    @field_validator('type')
    @classmethod
    def check_type(cls, v):
        if v != 'object':
            raise ValueError(f"Expected 'object' type, got '{v}'")
        return v

    @field_validator('additionalProperties')
    @classmethod
    def check_additional(cls, v):
        # We expect strict schema, so additionalProperties should be false
        if v is not False:
            print(f"Warning: additionalProperties is {v}, expected False for strict schema.")
        return v

def load_schema(path: Path) -> dict:
    """Load YAML schema file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema_dict: dict) -> bool:
    """Validate that the loaded YAML conforms to the expected schema structure."""
    try:
        model = DatasetSchema(**schema_dict)
        print(f"✓ Schema structure is valid: {model.type} schema loaded.")
        print(f"  - Required fields: {len(model.required)}")
        print(f"  - Properties defined: {len(model.properties)}")
        return True
    except ValidationError as e:
        print("✗ Schema structure validation failed:")
        print(e)
        return False

def validate_properties(schema_dict: dict) -> bool:
    """Perform specific checks on the properties defined in the schema."""
    props = schema_dict.get('properties', {})
    required = schema_dict.get('required', [])
    valid = True

    # Check for critical columns mentioned in T007
    critical_cols = ['household_id', 'CSA_Index', 'Stability_Score', 'HFIAS']
    for col in critical_cols:
        if col not in props:
            print(f"✗ Missing critical column in schema: {col}")
            valid = False
        elif col not in required:
            print(f"⚠ Column {col} is defined but not marked as required.")
            # Not strictly a failure, but a warning

    # Check data types for critical columns
    type_checks = {
        'household_id': 'string',
        'CSA_Index': 'number',
        'Stability_Score': 'number',
        'HFIAS': 'number',
        'latitude': 'number',
        'longitude': 'number',
        'finance_access': 'integer' # Enum 0/1
    }

    for col, expected_type in type_checks.items():
        if col in props:
            prop_def = props[col]
            actual_type = prop_def.get('type')
            if actual_type != expected_type:
                print(f"✗ Type mismatch for {col}: expected {expected_type}, got {actual_type}")
                valid = False
            else:
                print(f"✓ Type correct for {col}: {expected_type}")

    return valid

def main():
    print(f"Loading schema from: {SCHEMA_PATH}")
    try:
        schema_data = load_schema(SCHEMA_PATH)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)

    print("\n--- Validating Schema Structure ---")
    structure_valid = validate_schema_structure(schema_data)

    print("\n--- Validating Properties ---")
    properties_valid = validate_properties(schema_data)

    if structure_valid and properties_valid:
        print("\n✓ All validation checks passed. Schema is valid.")
        sys.exit(0)
    else:
        print("\n✗ Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()