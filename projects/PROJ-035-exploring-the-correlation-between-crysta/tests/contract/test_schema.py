"""
Contract test for merged_perovskite.schema.yaml.
Validates that the merged dataset conforms to the defined schema.
"""
import pytest
import yaml
import pandas as pd
from pathlib import Path
import sys
import jsonschema

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

SCHEMA_PATH = project_root / "contracts" / "merged_perovskite.schema.yaml"

@pytest.fixture
def schema():
    """Load the schema from the YAML file."""
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame that should conform to the schema."""
    return pd.DataFrame({
        'structure_id': ['mp-12345', 'mp-67890'],
        'thermal_conductivity': [10.5, 15.2],
        'source_reference': ['10.1000/journal.123', 'NIST-ABC123'],
        'chemistry_class': ['oxide', 'halide'],
        'temperature': [300.0, 305.0],
        'tilting_angle': [12.5, 10.2],
        'bond_length_variance': [0.001, 0.002],
        'tolerance_factor': [0.98, 1.02],
        'unit_cell_volume': [100.5, 105.2]
    })

@pytest.fixture
def invalid_dataframe_missing_field():
    """Create a DataFrame missing a required field."""
    return pd.DataFrame({
        'structure_id': ['mp-12345'],
        'thermal_conductivity': [10.5],
        'source_reference': ['10.1000/journal.123'],
        'chemistry_class': ['oxide'],
        'temperature': [300.0],
        'tilting_angle': [12.5],
        'bond_length_variance': [0.001],
        # Missing 'tolerance_factor' and 'unit_cell_volume'
    })

@pytest.fixture
def invalid_dataframe_wrong_type():
    """Create a DataFrame with wrong data types."""
    return pd.DataFrame({
        'structure_id': ['mp-12345'],
        'thermal_conductivity': ['not_a_number'],  # Should be number
        'source_reference': ['10.1000/journal.123'],
        'chemistry_class': ['oxide'],
        'temperature': [300.0],
        'tilting_angle': [12.5],
        'bond_length_variance': [0.001],
        'tolerance_factor': [0.98],
        'unit_cell_volume': [100.5]
    })

@pytest.fixture
def invalid_dataframe_bad_reference():
    """Create a DataFrame with an invalid source_reference format."""
    return pd.DataFrame({
        'structure_id': ['mp-12345'],
        'thermal_conductivity': [10.5],
        'source_reference': ['invalid_reference'],  # Doesn't match pattern
        'chemistry_class': ['oxide'],
        'temperature': [300.0],
        'tilting_angle': [12.5],
        'bond_length_variance': [0.001],
        'tolerance_factor': [0.98],
        'unit_cell_volume': [100.5]
    })

def test_schema_loads(schema):
    """Test that the schema file loads correctly."""
    assert schema is not None
    assert schema['type'] == 'object'
    assert 'properties' in schema
    assert 'required' in schema

def test_valid_dataframe_conforms(schema, sample_dataframe):
    """Test that a valid DataFrame conforms to the schema."""
    # Convert DataFrame to list of dicts for jsonschema validation
    records = sample_dataframe.to_dict('records')
    
    for record in records:
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Valid record failed schema validation: {e.message}")

def test_missing_required_field_fails(schema, invalid_dataframe_missing_field):
    """Test that a DataFrame missing required fields fails validation."""
    records = invalid_dataframe_missing_field.to_dict('records')
    record = records[0]
    
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=record, schema=schema)

def test_wrong_type_fails(schema, invalid_dataframe_wrong_type):
    """Test that a DataFrame with wrong data types fails validation."""
    records = invalid_dataframe_wrong_type.to_dict('records')
    record = records[0]
    
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=record, schema=schema)

def test_bad_reference_pattern_fails(schema, invalid_dataframe_bad_reference):
    """Test that a DataFrame with invalid source_reference fails validation."""
    records = invalid_dataframe_bad_reference.to_dict('records')
    record = records[0]
    
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=record, schema=schema)

def test_all_required_fields_present(schema):
    """Test that all required fields are defined in the schema."""
    required_fields = set(schema['required'])
    properties = set(schema['properties'].keys())
    
    assert required_fields.issubset(properties), \
        f"Required fields {required_fields - properties} not found in properties"

def test_schema_field_definitions(schema):
    """Test that schema fields have proper type definitions."""
    expected_fields = {
        'structure_id': 'string',
        'thermal_conductivity': 'number',
        'source_reference': 'string',
        'chemistry_class': 'string',
        'temperature': 'number',
        'tilting_angle': 'number',
        'bond_length_variance': 'number',
        'tolerance_factor': 'number',
        'unit_cell_volume': 'number'
    }
    
    for field, expected_type in expected_fields.items():
        assert field in schema['properties'], f"Field {field} missing from schema"
        assert schema['properties'][field]['type'] == expected_type, \
            f"Field {field} has wrong type: expected {expected_type}, got {schema['properties'][field]['type']}"