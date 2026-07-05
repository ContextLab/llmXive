"""
Contract tests for data schema validation.

Validates that parsed galaxy data conforms to the schema defined in
contracts/dataset.schema.yaml.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
schema_path = project_root / "contracts" / "dataset.schema.yaml"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the contracts directory."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str, field_path: str) -> List[str]:
    """Validate that a value matches the expected JSON schema type."""
    errors = []
    
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_path}: expected string, got {type(value).__name__}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)):
            errors.append(f"{field_path}: expected number, got {type(value).__name__}")
    elif expected_type == "integer":
        if not isinstance(value, int):
            errors.append(f"{field_path}: expected integer, got {type(value).__name__}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{field_path}: expected boolean, got {type(value).__name__}")
    elif expected_type == "array":
        if not isinstance(value, list):
            errors.append(f"{field_path}: expected array, got {type(value).__name__}")
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_path}: expected object, got {type(value).__name__}")
    
    return errors

def validate_constraints(value: Any, constraints: Dict[str, Any], field_path: str) -> List[str]:
    """Validate numeric constraints like minimum/maximum."""
    errors = []
    
    if isinstance(value, (int, float)):
        if "minimum" in constraints and value < constraints["minimum"]:
            errors.append(f"{field_path}: value {value} is less than minimum {constraints['minimum']}")
        if "maximum" in constraints and value > constraints["maximum"]:
            errors.append(f"{field_path}: value {value} is greater than maximum {constraints['maximum']}")
    
    return errors

def validate_array_items(value: Any, items_schema: Dict[str, Any], field_path: str) -> List[str]:
    """Validate array items against their schema."""
    errors = []
    
    if not isinstance(value, list):
        return errors
    
    min_items = items_schema.get("minItems", 0)
    if len(value) < min_items:
        errors.append(f"{field_path}: array has {len(value)} items, minimum is {min_items}")
    
    item_schema = items_schema.get("items", {})
    required_items = item_schema.get("required", [])
    item_props = item_schema.get("properties", {})
    
    for idx, item in enumerate(value):
        item_path = f"{field_path}[{idx}]"
        
        # Check required fields
        for req_field in required_items:
            if req_field not in item:
                errors.append(f"{item_path}: missing required field '{req_field}'")
        
        # Validate each property
        for prop_name, prop_value in item.items():
            if prop_name in item_props:
                prop_schema = item_props[prop_name]
                prop_path = f"{item_path}.{prop_name}"
                
                # Type check
                if "type" in prop_schema:
                    errors.extend(validate_type(prop_value, prop_schema["type"], prop_path))
                
                # Constraint check
                errors.extend(validate_constraints(prop_value, prop_schema, prop_path))
    
    return errors

def validate_object(value: Any, schema: Dict[str, Any], field_path: str = "root") -> List[str]:
    """Validate an object against a schema."""
    errors = []
    
    if not isinstance(value, dict):
        errors.append(f"{field_path}: expected object, got {type(value).__name__}")
        return errors
    
    # Check required fields
    required = schema.get("required", [])
    for req_field in required:
        if req_field not in value:
            errors.append(f"{field_path}: missing required field '{req_field}'")
    
    # Validate properties
    properties = schema.get("properties", {})
    for prop_name, prop_value in value.items():
        if prop_name in properties:
            prop_schema = properties[prop_name]
            prop_path = f"{field_path}.{prop_name}"
            
            # Type check
            if "type" in prop_schema:
                errors.extend(validate_type(prop_value, prop_schema["type"], prop_path))
            
            # Constraint check
            errors.extend(validate_constraints(prop_value, prop_schema, prop_path))
            
            # Array items check
            if prop_schema.get("type") == "array" and "items" in prop_schema:
                errors.extend(validate_array_items(prop_value, prop_schema, prop_path))
        elif "additionalProperties" in schema and schema["additionalProperties"] is False:
            errors.append(f"{field_path}: unexpected field '{prop_name}'")
    
    return errors

def validate_galaxy_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate galaxy data against the SPARC dataset schema.
    
    Args:
        data: Dictionary containing galaxy data to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    schema = load_schema()
    return validate_object(data, schema, "galaxy")

class TestSchemaValidation:
    """Test cases for schema validation."""
    
    @pytest.fixture
    def valid_galaxy_data(self) -> Dict[str, Any]:
        """Create valid sample galaxy data."""
        return {
            "galaxy_id": "UGC00001",
            "distance": 10.5,
            "inclination": 45.0,
            "inclination_uncertainty": 2.0,
            "hubble_type": "Sc",
            "rotation_curve": [
                {
                    "radial_distance": 1.0,
                    "velocity": 50.0,
                    "velocity_uncertainty": 2.5
                },
                {
                    "radial_distance": 2.0,
                    "velocity": 80.0,
                    "velocity_uncertainty": 3.0
                }
            ]
        }
    
    def test_valid_galaxy_data(self, valid_galaxy_data):
        """Test that valid galaxy data passes validation."""
        errors = validate_galaxy_data(valid_galaxy_data)
        assert len(errors) == 0, f"Valid data failed validation: {errors}"
    
    def test_missing_required_field(self, valid_galaxy_data):
        """Test validation fails when required field is missing."""
        del valid_galaxy_data["galaxy_id"]
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("missing required field 'galaxy_id'" in e for e in errors)
    
    def test_invalid_type_string(self, valid_galaxy_data):
        """Test validation fails when string field gets number."""
        valid_galaxy_data["galaxy_id"] = 12345
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("expected string" in e for e in errors)
    
    def test_invalid_type_number(self, valid_galaxy_data):
        """Test validation fails when number field gets string."""
        valid_galaxy_data["distance"] = "ten"
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("expected number" in e for e in errors)
    
    def test_minimum_constraint_violation(self, valid_galaxy_data):
        """Test validation fails when minimum constraint is violated."""
        valid_galaxy_data["distance"] = -5.0
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("less than minimum" in e for e in errors)
    
    def test_maximum_constraint_violation(self, valid_galaxy_data):
        """Test validation fails when maximum constraint is violated."""
        valid_galaxy_data["inclination"] = 100.0
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("greater than maximum" in e for e in errors)
    
    def test_empty_rotation_curve(self, valid_galaxy_data):
        """Test validation fails when rotation curve is empty."""
        valid_galaxy_data["rotation_curve"] = []
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("minimum is 1" in e for e in errors)
    
    def test_missing_rotation_curve_field(self, valid_galaxy_data):
        """Test validation fails when rotation curve item is missing required field."""
        valid_galaxy_data["rotation_curve"][0].pop("velocity")
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("missing required field 'velocity'" in e for e in errors)
    
    def test_invalid_rotation_curve_type(self, valid_galaxy_data):
        """Test validation fails when rotation curve field has wrong type."""
        valid_galaxy_data["rotation_curve"][0]["radial_distance"] = "1.0"
        errors = validate_galaxy_data(valid_galaxy_data)
        assert any("expected number" in e for e in errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
