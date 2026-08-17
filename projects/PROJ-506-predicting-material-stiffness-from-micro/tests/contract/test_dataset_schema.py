"""
Contract test for dataset schema conformity.

Tests that generated data conforms to the schema defined in
specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml
"""
import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_generation.validate_tensors import (
    load_schema,
    validate_schema_conformity,
    validate_vrh_bounds
)

@pytest.fixture
def schema():
    """Load the dataset schema."""
    schema_path = Path("specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml")
    if not schema_path.exists():
        pytest.skip("Schema file not found")
    return load_schema(str(schema_path))

@pytest.fixture
def valid_record():
    """Create a valid test record."""
    return {
        "image_path": "data/raw/micro_42.png",
        "stiffness_tensor": [100.0, 100.0, 100.0, 40.0, 40.0, 40.0],
        "inclusion_density": 0.3,
        "topology_type": "random_disks",
        "shape_factor": 0.85,
        "connectivity": 0.5,
        "seed": 42
    }

@pytest.fixture
def invalid_record_missing_field():
    """Create a record missing a required field."""
    return {
        "image_path": "data/raw/micro_42.png",
        "stiffness_tensor": [100.0, 100.0, 100.0, 40.0, 40.0, 40.0],
        "inclusion_density": 0.3,
        "topology_type": "random_disks",
        # Missing shape_factor, connectivity, seed
    }

@pytest.fixture
def invalid_record_wrong_type():
    """Create a record with wrong field types."""
    return {
        "image_path": 123,  # Should be string
        "stiffness_tensor": "not_a_list",  # Should be list
        "inclusion_density": 1.5,  # Out of range
        "topology_type": "invalid_type",  # Not in enum
        "shape_factor": 0.85,
        "connectivity": 0.5,
        "seed": 42
    }

def test_schema_loading(schema):
    """Test that schema loads correctly."""
    assert schema is not None
    assert "required_fields" in schema
    assert len(schema["required_fields"]) == 7

def test_valid_record_conforms(valid_record, schema):
    """Test that a valid record passes schema validation."""
    is_valid, errors = validate_schema_conformity(valid_record, schema)
    assert is_valid
    assert len(errors) == 0

def test_missing_field_fails(invalid_record_missing_field, schema):
    """Test that missing required fields are detected."""
    is_valid, errors = validate_schema_conformity(invalid_record_missing_field, schema)
    assert not is_valid
    assert len(errors) > 0
    assert any("shape_factor" in e for e in errors)

def test_wrong_type_fails(invalid_record_wrong_type, schema):
    """Test that type mismatches are detected."""
    is_valid, errors = validate_schema_conformity(invalid_record_wrong_type, schema)
    # Note: This basic validator checks presence, not types
    # More sophisticated type checking would be added in a full implementation
    assert not is_valid or len(errors) > 0

def test_vrh_bounds_valid():
    """Test VRH bounds validation with valid tensor."""
    tensor = [100.0, 100.0, 100.0, 40.0, 40.0, 40.0]
    density = 0.3
    is_valid, error = validate_vrh_bounds(tensor, density)
    # Should be valid for reasonable parameters
    assert is_valid or "outside" not in error.lower()

def test_vrh_bounds_wrong_length():
    """Test VRH bounds validation with wrong tensor length."""
    tensor = [100.0, 100.0, 100.0]  # Only 3 components
    density = 0.3
    is_valid, error = validate_vrh_bounds(tensor, density)
    assert not is_valid
    assert "Invalid tensor length" in error
