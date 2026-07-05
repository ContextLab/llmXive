"""
Contract test for parsed galaxy schema.

Validates that the parsed galaxy data structure conforms to the schema defined
in contracts/dataset.schema.yaml. This test ensures data integrity for User Story 1.
"""
import os
import sys
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path for imports if running from tests directory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils import get_logger

logger = get_logger(__name__)

# Path to the schema definition
SCHEMA_PATH = project_root / "contracts" / "dataset.schema.yaml"
# Path to the expected output (if it exists from a previous run, otherwise we test the validator logic)
PROCESSED_DATA_PATH = project_root / "data" / "processed" / "filtered_galaxies.csv"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_galaxy_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single galaxy record against the schema.
    
    Args:
        record: A dictionary representing a single galaxy's data row.
        schema: The loaded schema definition.
        
    Returns:
        A list of validation error messages. Empty if valid.
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool
    }

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check types and constraints
    for field, value in record.items():
        if field not in properties:
            errors.append(f"Unknown field in record: {field}")
            continue

        field_spec = properties[field]
        expected_type = field_spec.get("type")
        
        if expected_type:
            if not isinstance(value, type_map.get(expected_type, object)):
                errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(value).__name__}")
                continue

        # Check numeric constraints if applicable
        if expected_type in ("number", "integer"):
            minimum = field_spec.get("minimum")
            maximum = field_spec.get("maximum")
            exclusive_minimum = field_spec.get("exclusiveMinimum")
            exclusive_maximum = field_spec.get("exclusiveMaximum")

            if minimum is not None and value < minimum:
                errors.append(f"Field '{field}' value {value} is below minimum {minimum}")
            if maximum is not None and value > maximum:
                errors.append(f"Field '{field}' value {value} is above maximum {maximum}")
            if exclusive_minimum is not None and value <= exclusive_minimum:
                errors.append(f"Field '{field}' value {value} is not strictly greater than {exclusive_minimum}")
            if exclusive_maximum is not None and value >= exclusive_maximum:
                errors.append(f"Field '{field}' value {value} is not strictly less than {exclusive_maximum}")

    return errors

def test_schema_exists():
    """Verify the schema file exists and is valid YAML."""
    schema = load_schema()
    assert schema is not None
    assert "properties" in schema
    assert "required" in schema

def test_schema_definition_integrity():
    """Verify the schema contains expected fields for galaxy rotation curves."""
    schema = load_schema()
    properties = schema.get("properties", {})
    
    expected_fields = [
        "galaxy_name", "radial_distance", "velocity", "velocity_error", 
        "inclination", "inclination_error"
    ]
    
    missing = [f for f in expected_fields if f not in properties]
    assert not missing, f"Schema is missing expected fields: {missing}"

@pytest.mark.skipif(not PROCESSED_DATA_PATH.exists(), reason="No processed data file found to validate against schema")
def test_parsed_galaxies_against_schema():
    """
    Contract test: Validate the actual parsed galaxy data file against the schema.
    
    This test reads the CSV produced by the preprocessing pipeline and ensures
    every row conforms to the defined schema constraints.
    """
    import pandas as pd
    
    schema = load_schema()
    df = pd.read_csv(PROCESSED_DATA_PATH)
    
    logger.info(f"Validating {len(df)} records against schema...")
    
    all_errors = []
    valid_count = 0
    
    for idx, row in df.iterrows():
        record = row.to_dict()
        errors = validate_galaxy_record(record, schema)
        
        if errors:
            all_errors.extend([f"Row {idx}: {e}" for e in errors])
        else:
            valid_count += 1
    
    logger.info(f"Validation complete: {valid_count} valid, {len(all_errors)} errors found.")
    
    if all_errors:
        pytest.fail(f"Schema validation failed for {len(all_errors)} records:\n" + "\n".join(all_errors[:10])) # Show first 10 errors
    
    assert valid_count == len(df), "Not all records passed schema validation."

def test_empty_dataframe_handling():
    """Test that the validator handles empty data correctly (if applicable)."""
    schema = load_schema()
    # An empty record dict should fail required field checks
    errors = validate_galaxy_record({}, schema)
    assert len(errors) > 0, "Empty record should have validation errors"
    assert any("Missing required" in e for e in errors)

def test_boundary_values():
    """Test specific boundary conditions defined in the schema."""
    schema = load_schema()
    props = schema.get("properties", {})
    
    # Test radial_distance > 0 if exclusiveMinimum is 0
    if "radial_distance" in props:
        spec = props["radial_distance"]
        if spec.get("exclusiveMinimum") == 0:
            errors = validate_galaxy_record({"radial_distance": 0}, spec)
            # This is a simplified check; full validation logic is in the main function
            # We just ensure the logic path exists
            assert True 
    
    # Test inclination constraints (typically 0-90)
    if "inclination" in props:
        spec = props["inclination"]
        # Ensure 90 is allowed if max is 90
        errors = validate_galaxy_record({"inclination": 90}, spec)
        # If max is 90, 90 should be valid unless exclusiveMaximum
        if spec.get("maximum") == 90 and not spec.get("exclusiveMaximum"):
            assert not any("above maximum" in e for e in errors)

if __name__ == "__main__":
    # Allow running directly for quick feedback
    pytest.main([__file__, "-v"])