"""
Contract test for descriptor output schema.

This test validates that descriptor vector outputs conform to the 
JSON Schema contract defined in contracts/descriptor_vector.schema.json.

Per task T008: This must run before implementation to establish the 
contract that the descriptor computation module must satisfy.
"""
import json
import os
import pytest
from pathlib import Path

try:
    import jsonschema
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

# Project root is the parent of tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "descriptor_vector.schema.json"

# Sample data that should pass validation once implementation produces it
VALID_DESCRIPTORS_SAMPLE = {
    "data": [
        {
            "sample_id": "alloy_001",
            "composition": "Cu50Zr50",
            "elemental_symbols": ["Cu", "Zr"],
            "stoichiometry": [0.5, 0.5],
            "atomic_size_mismatch": 0.085,
            "mixing_enthalpy": -12.5,
            "electronegativity_variance": 0.15,
            "phase_label": "glass",
            "source": "experimental",
            "experimental_validation_status": "yes"
        },
        {
            "sample_id": "alloy_002",
            "composition": "Cu60Zr40",
            "elemental_symbols": ["Cu", "Zr"],
            "stoichiometry": [0.6, 0.4],
            "atomic_size_mismatch": 0.092,
            "mixing_enthalpy": -11.8,
            "electronegativity_variance": 0.18,
            "phase_label": "crystalline",
            "source": "experimental",
            "experimental_validation_status": "yes"
        }
    ],
    "metadata": {
        "descriptor_version": "1.0.0",
        "computation_date": "2024-01-15",
        "parameters": {
            "atomic_radii_source": "pymatgen",
            "electronegativity_scale": "pauling"
        }
    }
}

# Sample data that should fail validation
INVALID_DESCRIPTORS_SAMPLE = {
    "data": [
        {
            "sample_id": "alloy_003",
            "composition": "Cu50Zr50",
            "elemental_symbols": ["Cu", "Zr"],
            "stoichiometry": [0.5, 0.5],
            "atomic_size_mismatch": "not_a_number",  # Invalid: should be float
            "mixing_enthalpy": -12.5,
            "electronegativity_variance": 0.15,
            "phase_label": "unknown",  # Invalid: should be 'glass' or 'crystalline'
            "source": "experimental",
            "experimental_validation_status": "yes"
        }
    ],
    "metadata": {}
}

@pytest.fixture
def schema():
    """Load the descriptor_vector schema from contracts."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return json.load(f)

@pytest.fixture
def valid_sample():
    """Return a valid descriptor sample."""
    return VALID_DESCRIPTORS_SAMPLE

@pytest.fixture
def invalid_sample():
    """Return an invalid descriptor sample."""
    return INVALID_DESCRIPTORS_SAMPLE

class TestDescriptorSchemaContract:
    """Contract tests for descriptor_vector schema validation."""
    
    def test_schema_file_exists(self):
        """Verify the schema contract file exists."""
        assert SCHEMA_PATH.exists(), (
            f"Schema file {SCHEMA_PATH} must exist for contract validation. "
            "Run task T004 to create the schema contracts."
        )
    
    def test_schema_is_valid_json(self, schema):
        """Verify the schema file is valid JSON."""
        assert isinstance(schema, dict), "Schema must be a JSON object"
        assert "$schema" in schema or "type" in schema, (
            "Schema must contain $schema or type field"
        )
    
    def test_schema_has_required_properties(self, schema):
        """Verify the schema defines required properties for descriptor output."""
        assert "type" in schema, "Schema must specify type"
        assert schema["type"] == "object", "Descriptor output must be an object"
        
        # Check that 'data' and 'metadata' are defined in properties
        properties = schema.get("properties", {})
        assert "data" in properties, "Schema must define 'data' property"
        assert "metadata" in properties, "Schema must define 'metadata' property"
    
    def test_valid_sample_passes_validation(self, schema, valid_sample):
        """Verify valid descriptor samples pass schema validation."""
        try:
            jsonschema.validate(instance=valid_sample, schema=schema)
        except jsonschema.ValidationError as e:
            pytest.fail(
                f"Valid sample failed validation: {e.message}. "
                "This indicates the schema contract may be incorrect or "
                "the sample data needs adjustment."
            )
    
    def test_invalid_sample_fails_validation(self, schema, invalid_sample):
        """Verify invalid descriptor samples fail schema validation."""
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_sample, schema=schema)
    
    def test_sample_id_is_string(self, schema):
        """Verify sample_id field is defined as string type."""
        data_schema = schema.get("properties", {}).get("data", {})
        items_schema = data_schema.get("items", {})
        properties = items_schema.get("properties", {})
        
        assert "sample_id" in properties, "sample_id must be defined"
        assert properties["sample_id"].get("type") == "string", (
            "sample_id must be a string"
        )
    
    def test_composition_is_string(self, schema):
        """Verify composition field is defined as string type."""
        data_schema = schema.get("properties", {}).get("data", {})
        items_schema = data_schema.get("items", {})
        properties = items_schema.get("properties", {})
        
        assert "composition" in properties, "composition must be defined"
        assert properties["composition"].get("type") == "string", (
            "composition must be a string"
        )
    
    def test_numeric_descriptors_are_numbers(self, schema):
        """Verify numeric descriptor fields are defined as number type."""
        data_schema = schema.get("properties", {}).get("data", {})
        items_schema = data_schema.get("items", {})
        properties = items_schema.get("properties", {})
        
        numeric_fields = [
            "atomic_size_mismatch",
            "mixing_enthalpy", 
            "electronegativity_variance"
        ]
        
        for field in numeric_fields:
            assert field in properties, f"{field} must be defined"
            field_type = properties[field].get("type")
            assert field_type in ("number", "integer"), (
                f"{field} must be a number type, got {field_type}"
            )
    
    def test_phase_label_enum(self, schema):
        """Verify phase_label is an enum with valid values."""
        data_schema = schema.get("properties", {}).get("data", {})
        items_schema = data_schema.get("items", {})
        properties = items_schema.get("properties", {})
        
        assert "phase_label" in properties, "phase_label must be defined"
        enum_values = properties["phase_label"].get("enum", [])
        assert "glass" in enum_values, "phase_label must include 'glass'"
        assert "crystalline" in enum_values, "phase_label must include 'crystalline'"
    
    def test_schema_validates_against_jsonschema_spec(self):
        """Verify the schema itself is valid JSON Schema."""
        with open(SCHEMA_PATH, 'r') as f:
            schema = json.load(f)
        
        # Basic JSON Schema validation
        assert "$schema" in schema or "type" in schema, (
            "Schema must declare its type or $schema version"
        )
    
    def test_required_fields_in_schema(self, schema):
        """Verify required fields are marked as required in schema."""
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        assert "data" in required, "data must be a required field"
        assert "metadata" in required, "metadata must be a required field"
    
    def test_metadata_structure(self, schema):
        """Verify metadata structure is properly defined."""
        metadata_schema = schema.get("properties", {}).get("metadata", {})
        
        # Metadata should be an object
        assert metadata_schema.get("type") == "object", (
            "metadata must be an object"
        )
    
    def test_descriptor_version_in_metadata(self, schema):
        """Verify descriptor_version is defined in metadata."""
        metadata_schema = schema.get("properties", {}).get("metadata", {})
        metadata_props = metadata_schema.get("properties", {})
        
        assert "descriptor_version" in metadata_props, (
            "descriptor_version must be defined in metadata"
        )