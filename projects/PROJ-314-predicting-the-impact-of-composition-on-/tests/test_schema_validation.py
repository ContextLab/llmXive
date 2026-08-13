"""
Unit tests for T012a schema validation logic.
"""
import pytest
import yaml
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to allow imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from contracts.validate_schemas import (
    load_yaml_file, 
    validate_schema_fields, 
    REQUIRED_CERAMIC_ENTRY_FIELDS,
    REQUIRED_MODEL_RESULT_FIELDS
)

def test_load_yaml_file_valid():
    """Test loading a valid YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("properties:\n  field1: {type: string}\n")
        temp_path = Path(f.name)
    
    try:
        data = load_yaml_file(temp_path)
        assert 'properties' in data
        assert 'field1' in data['properties']
    finally:
        temp_path.unlink()

def test_load_yaml_file_missing():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_yaml_file(Path("/nonexistent/path/schema.yaml"))

def test_validate_schema_fields_all_present():
    """Test validation when all required fields are present."""
    schema = {
        "properties": {
            "composition": {"type": "string"},
            "weibull_modulus": {"type": "number"},
            "sample_count": {"type": "integer"},
            "is_range_flag": {"type": "boolean"},
            "range_original": {"type": "string"},
            "primary_anion_cation_group": {"type": "string"},
            "sintering_temp": {"type": "number"},
            "is_imputed": {"type": "boolean"},
            "mean_atomic_radius": {"type": "number"},
            "electronegativity_std": {"type": "number"},
            "valence_electron_concentration": {"type": "number"},
            "extra_field": {"type": "string"}
        }
    }
    
    errors = validate_schema_fields(schema, REQUIRED_CERAMIC_ENTRY_FIELDS, "test_schema")
    assert len(errors) == 0

def test_validate_schema_fields_missing():
    """Test validation when some required fields are missing."""
    schema = {
        "properties": {
            "composition": {"type": "string"},
            # Missing most other fields
        }
    }
    
    errors = validate_schema_fields(schema, REQUIRED_CERAMIC_ENTRY_FIELDS, "test_schema")
    assert len(errors) == 1
    assert "missing required fields" in errors[0].lower()
    assert "weibull_modulus" in errors[0]

def test_validate_schema_fields_no_properties():
    """Test validation when properties key is missing."""
    schema = {
        "type": "object"
        # No properties key
    }
    
    errors = validate_schema_fields(schema, REQUIRED_CERAMIC_ENTRY_FIELDS, "test_schema")
    assert len(errors) == 1
    assert "missing 'properties' definition" in errors[0]

def test_required_fields_defined():
    """Ensure required field sets are not empty."""
    assert len(REQUIRED_CERAMIC_ENTRY_FIELDS) > 0
    assert len(REQUIRED_MODEL_RESULT_FIELDS) > 0
    assert "weibull_modulus" in REQUIRED_CERAMIC_ENTRY_FIELDS
    assert "mae" in REQUIRED_MODEL_RESULT_FIELDS