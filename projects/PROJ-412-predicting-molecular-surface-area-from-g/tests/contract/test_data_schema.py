"""
Contract test for data schema validation.

Validates that processed molecular data conforms to the static schema
defined in data/schema.yaml before further processing or model training.

This test ensures input format compliance as required by User Story 1 (US1).
"""
import json
import yaml
import os
import sys
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

SCHEMA_PATH = project_root / "data" / "schema.yaml"
SAMPLE_DATA_PATH = project_root / "data" / "processed" / "sample_processed_data.json"

def load_schema() -> Dict[str, Any]:
    """Load the static schema from YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str, field_path: str) -> None:
    """Validate that a value matches the expected type."""
    type_map = {
        "string": str,
        "integer": int,
        "float": (int, float),
        "boolean": bool,
        "list": list,
        "object": dict
    }
    
    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        raise ValueError(f"Unknown type: {expected_type}")
    
    if not isinstance(value, expected_python_type):
        raise TypeError(
            f"Field '{field_path}' expected type '{expected_type}', "
            f"got {type(value).__name__}"
        )

def validate_field_constraints(value: Any, field_def: Dict[str, Any], field_path: str) -> None:
    """Validate field-specific constraints."""
    constraints = field_def.get("constraints", {})
    
    if "min" in constraints and isinstance(value, (int, float)):
        if value < constraints["min"]:
            raise ValueError(
                f"Field '{field_path}' value {value} is below minimum {constraints['min']}"
            )
    
    if "max" in constraints and isinstance(value, (int, float)):
        if value > constraints["max"]:
            raise ValueError(
                f"Field '{field_path}' value {value} is above maximum {constraints['max']}"
            )

def validate_list_schema(value: List[Any], item_schema: Dict[str, Any], field_path: str) -> None:
    """Validate a list against its item schema."""
    if not isinstance(value, list):
        raise TypeError(f"Field '{field_path}' expected list, got {type(value).__name__}")
    
    if "min_items" in item_schema:
        if len(value) < item_schema["min_items"]:
            raise ValueError(
                f"Field '{field_path}' has {len(value)} items, "
                f"minimum required is {item_schema['min_items']}"
            )
    
    if "max_items" in item_schema:
        if len(value) > item_schema["max_items"]:
            raise ValueError(
                f"Field '{field_path}' has {len(value)} items, "
                f"maximum allowed is {item_schema['max_items']}"
            )
    
    # Validate items if schema defines them
    if "items" in item_schema:
        item_def = item_schema["items"]
        for idx, item in enumerate(value):
            validate_type(item, item_def["type"], f"{field_path}[{idx}]")

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a single data record against the schema."""
    fields = schema.get("fields", [])
    field_map = {f["name"]: f for f in fields}
    
    # Check required fields
    for field in fields:
        field_name = field["name"]
        if field.get("required", False) and field_name not in record:
            raise KeyError(f"Required field missing: '{field_name}'")
    
    # Validate present fields
    for field_name, value in record.items():
        if field_name not in field_map:
            # Unknown field - could be strict or lenient. 
            # For contract tests, we flag unknown fields.
            raise KeyError(f"Unknown field in record: '{field_name}'")
        
        field_def = field_map[field_name]
        expected_type = field_def["type"]
        
        # Type validation
        validate_type(value, expected_type, field_name)
        
        # List schema validation
        if expected_type == "list" and "item_schema" in field_def:
            validate_list_schema(value, field_def["item_schema"], field_name)
        
        # Constraint validation
        validate_field_constraints(value, field_def, field_name)

def validate_dataset(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> None:
    """Validate an entire dataset (list of records) against the schema."""
    if not isinstance(data, list):
        raise TypeError("Dataset must be a list of records")
    
    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            raise TypeError(f"Record at index {idx} is not a dictionary")
        try:
            validate_record(record, schema)
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Validation failed for record at index {idx}: {e}")

@pytest.fixture
def schema():
    """Load the schema for tests."""
    return load_schema()

def test_schema_file_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

def test_schema_structure(schema):
    """Verify the schema has the expected top-level structure."""
    assert "version" in schema
    assert "fields" in schema
    assert isinstance(schema["fields"], list)
    assert len(schema["fields"]) > 0

def test_required_fields_defined(schema):
    """Verify all critical required fields are defined in the schema."""
    field_names = {f["name"] for f in schema["fields"]}
    required_critical_fields = {"molecule_id", "smiles", "sasa", "atom_features", "edge_index"}
    missing = required_critical_fields - field_names
    assert not missing, f"Critical fields missing from schema: {missing}"

def test_validate_valid_record(schema):
    """Test validation passes for a correctly formatted record."""
    valid_record = {
        "molecule_id": "ZINC12345",
        "smiles": "CCO",
        "atom_features": [[6.0, 0.0, 0.0], [6.0, 0.0, 0.0], [8.0, 0.0, 0.0]],
        "edge_index": [[0, 1, 1], [1, 0, 2]],
        "sasa": 45.6,
        "num_atoms": 3,
        "num_bonds": 2,
        "source": "zinc15_filtered"
    }
    validate_record(valid_record, schema)

def test_validate_invalid_type(schema):
    """Test validation fails for incorrect types."""
    invalid_record = {
        "molecule_id": 12345,  # Should be string
        "smiles": "CCO",
        "atom_features": [[6.0, 0.0, 0.0]],
        "edge_index": [[0, 1], [1, 0]],
        "sasa": 45.6,
        "num_atoms": 3,
        "num_bonds": 2,
        "source": "zinc15_filtered"
    }
    with pytest.raises(TypeError):
        validate_record(invalid_record, schema)

def test_validate_missing_required_field(schema):
    """Test validation fails when a required field is missing."""
    invalid_record = {
        "molecule_id": "ZINC12345",
        "smiles": "CCO",
        "atom_features": [[6.0, 0.0, 0.0]],
        "edge_index": [[0, 1], [1, 0]],
        "num_atoms": 3,
        "num_bonds": 2,
        "source": "zinc15_filtered"
        # Missing 'sasa' which is required
    }
    with pytest.raises(KeyError):
        validate_record(invalid_record, schema)

def test_validate_sasa_constraints(schema):
    """Test validation fails for SASA violating constraints."""
    invalid_record = {
        "molecule_id": "ZINC12345",
        "smiles": "CCO",
        "atom_features": [[6.0, 0.0, 0.0]],
        "edge_index": [[0, 1], [1, 0]],
        "sasa": -5.0,  # Negative SASA violates min: 0.0
        "num_atoms": 3,
        "num_bonds": 2,
        "source": "zinc15_filtered"
    }
    with pytest.raises(ValueError):
        validate_record(invalid_record, schema)

def test_validate_empty_atom_features(schema):
    """Test validation fails for empty atom features."""
    invalid_record = {
        "molecule_id": "ZINC12345",
        "smiles": "CCO",
        "atom_features": [],  # Empty list violates min_items: 1
        "edge_index": [[0, 1], [1, 0]],
        "sasa": 45.6,
        "num_atoms": 3,
        "num_bonds": 2,
        "source": "zinc15_filtered"
    }
    with pytest.raises(ValueError):
        validate_record(invalid_record, schema)

def test_validate_unknown_field(schema):
    """Test validation fails for unknown fields."""
    invalid_record = {
        "molecule_id": "ZINC12345",
        "smiles": "CCO",
        "atom_features": [[6.0, 0.0, 0.0]],
        "edge_index": [[0, 1], [1, 0]],
        "sasa": 45.6,
        "num_atoms": 3,
        "num_bonds": 2,
        "source": "zinc15_filtered",
        "unknown_field": "should_fail"
    }
    with pytest.raises(KeyError):
        validate_record(invalid_record, schema)

@pytest.mark.integration
def test_validate_sample_processed_data(schema):
    """
    Integration test: Validate actual processed data if it exists.
    This test will be skipped if no sample data is available yet.
    """
    if not SAMPLE_DATA_PATH.exists():
        pytest.skip(f"Sample data file not found: {SAMPLE_DATA_PATH}")
    
    with open(SAMPLE_DATA_PATH, 'r') as f:
        data = json.load(f)
    
    # Data might be a list or a dict with a 'data' key
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    
    assert isinstance(data, list), "Processed data must be a list of records"
    validate_dataset(data, schema)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])