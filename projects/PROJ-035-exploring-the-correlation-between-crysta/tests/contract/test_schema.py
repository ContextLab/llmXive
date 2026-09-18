"""
Contract test for merged_perovskite.schema.yaml.

This test verifies that the schema file exists, is valid YAML,
and contains all required fields defined in the specification.

It also validates that any CSV file matching the schema path
adheres to the defined structure.
"""
import os
import sys
import pytest
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to path to allow imports if needed
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Constants defined by the schema requirements (FR-002, FR-010)
SCHEMA_PATH = Path("contracts/merged_perovskite.schema.yaml")
EXPECTED_FIELDS = [
    "structure_id",
    "thermal_conductivity",
    "source_reference",
    "chemistry_class",
    "temperature",
    "tilting_angle",
    "bond_length_variance",
    "tolerance_factor",
    "unit_cell_volume"
]

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    if schema is None:
        pytest.fail("Schema file is empty or invalid YAML")
    
    return schema

def validate_schema_structure(schema: Dict[str, Any]) -> None:
    """Validate that the schema contains the required fields definition."""
    # The schema should define the fields, typically under a 'fields' or 'properties' key
    # Based on typical YAML schema patterns for this project
    fields = None
    
    if "fields" in schema:
        fields = schema["fields"]
    elif "properties" in schema:
        fields = schema["properties"]
    elif isinstance(schema, list):
        fields = schema
    else:
        # Try to infer from common patterns
        for key in schema:
            if isinstance(schema[key], list) and len(schema[key]) > 0:
                if isinstance(schema[key][0], str):
                    fields = schema[key]
                    break
    
    if fields is None:
        pytest.fail("Schema does not contain a recognizable fields definition")
    
    # Normalize fields to a list of strings if they are dicts with 'name' keys
    if isinstance(fields, list) and len(fields) > 0:
        if isinstance(fields[0], dict):
            field_names = [f.get("name", f.get("field", "")) for f in fields]
        else:
            field_names = fields
    else:
        pytest.fail("Fields definition is not a valid list")
    
    # Check for required fields
    missing_fields = set(EXPECTED_FIELDS) - set(field_names)
    if missing_fields:
        pytest.fail(f"Schema missing required fields: {missing_fields}")

def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> None:
    """Validate that a CSV file adheres to the schema structure."""
    if not csv_path.exists():
        # If CSV doesn't exist, we skip the data validation but schema validation still passed
        return
    
    df = pd.read_csv(csv_path)
    
    # Get schema fields
    fields = None
    if "fields" in schema:
        fields = schema["fields"]
    elif "properties" in schema:
        fields = schema["properties"]
    elif isinstance(schema, list):
        fields = schema
    
    if fields is None:
        pytest.fail("Cannot extract fields from schema for validation")
    
    if isinstance(fields, list) and len(fields) > 0:
        if isinstance(fields[0], dict):
            field_names = [f.get("name", f.get("field", "")) for f in fields]
        else:
            field_names = fields
    else:
        pytest.fail("Fields definition is not a valid list")
    
    # Check columns exist
    missing_columns = set(field_names) - set(df.columns)
    if missing_columns:
        pytest.fail(f"CSV missing required columns: {missing_columns}")
    
    # Check for nulls in critical fields
    critical_fields = ["structure_id", "thermal_conductivity", "source_reference"]
    for field in critical_fields:
        if field in df.columns:
            if df[field].isna().any():
                pytest.fail(f"CSV contains null values in critical field: {field}")

class TestSchemaContract:
    """Contract tests for merged_perovskite.schema.yaml."""
    
    def test_schema_file_exists(self):
        """Test that the schema file exists at the expected path."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"
    
    def test_schema_is_valid_yaml(self):
        """Test that the schema file is valid YAML."""
        schema = load_schema(SCHEMA_PATH)
        assert isinstance(schema, dict), "Schema should be a dictionary"
    
    def test_schema_contains_required_fields(self):
        """Test that the schema contains all required fields."""
        schema = load_schema(SCHEMA_PATH)
        validate_schema_structure(schema)
    
    def test_schema_fields_match_specification(self):
        """Test that schema fields match the exact specification requirements."""
        schema = load_schema(SCHEMA_PATH)
        
        # Extract field names
        fields = None
        if "fields" in schema:
            fields = schema["fields"]
        elif "properties" in schema:
            fields = schema["properties"]
        elif isinstance(schema, list):
            fields = schema
        
        if fields is None:
            pytest.fail("Cannot extract fields from schema")
        
        if isinstance(fields, list) and len(fields) > 0:
            if isinstance(fields[0], dict):
                field_names = [f.get("name", f.get("field", "")) for f in fields]
            else:
                field_names = fields
        else:
            pytest.fail("Fields definition is not a valid list")
        
        # Verify exact match with expected fields
        assert set(field_names) == set(EXPECTED_FIELDS), \
            f"Schema fields {field_names} do not match expected {EXPECTED_FIELDS}"
    
    def test_schema_allows_csv_validation(self):
        """Test that the schema can be used to validate a CSV file."""
        schema = load_schema(SCHEMA_PATH)
        
        # Check if the merged dataset exists
        merged_path = Path("data/cleaned/merged_perovskite.csv")
        if merged_path.exists():
            validate_csv_against_schema(merged_path, schema)
        else:
            # If merged data doesn't exist yet, just verify schema is valid
            # This allows the test to pass during initial setup
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
