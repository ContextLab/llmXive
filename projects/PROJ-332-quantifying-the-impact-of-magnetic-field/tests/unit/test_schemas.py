"""
Unit tests for schema definitions (T007).
Validates that the YAML schema files are syntactically correct and loadable.
"""
import pytest
import yaml
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

@pytest.fixture
def dataset_schema_path():
    return CONTRACTS_DIR / "dataset.schema.yaml"

@pytest.fixture
def output_schema_path():
    return CONTRACTS_DIR / "output.schema.yaml"

def test_dataset_schema_exists_and_valid(dataset_schema_path):
    """Verify dataset.schema.yaml exists and is valid YAML."""
    assert dataset_schema_path.exists(), "contracts/dataset.schema.yaml not found"
    
    with open(dataset_schema_path, 'r') as f:
        try:
            schema = yaml.safe_load(f)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert 'type' in schema, "Schema must define a type"
            assert schema['type'] == 'object', "Root type must be object"
            assert 'properties' in schema, "Schema must define properties"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in dataset.schema.yaml: {e}")

def test_output_schema_exists_and_valid(output_schema_path):
    """Verify output.schema.yaml exists and is valid YAML."""
    assert output_schema_path.exists(), "contracts/output.schema.yaml not found"
    
    with open(output_schema_path, 'r') as f:
        try:
            schema = yaml.safe_load(f)
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert 'type' in schema, "Schema must define a type"
            assert schema['type'] == 'object', "Root type must be object"
            # Check for expected columns definition
            assert 'expected_columns' in schema, "Schema must define expected_columns"
            assert isinstance(schema['expected_columns'], list), "expected_columns must be a list"
            
            # Verify specific required columns exist
            col_names = [col['name'] for col in schema['expected_columns']]
            required_cols = ['discharge_id', 'island_width', 'tau_e', 'confinement_mode']
            for col in required_cols:
                assert col in col_names, f"Missing required column in schema: {col}"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in output.schema.yaml: {e}")

def test_schema_references_json_schema_draft(dataset_schema_path, output_schema_path):
    """Verify schemas reference a valid JSON Schema draft."""
    for path in [dataset_schema_path, output_schema_path]:
        with open(path, 'r') as f:
            schema = yaml.safe_load(f)
            assert '$schema' in schema, f"Schema {path} must define $schema"
            assert 'json-schema.org' in schema['$schema'], f"Schema {path} must reference json-schema.org"

def test_dataset_schema_has_required_fields(dataset_schema_path):
    """Verify dataset schema enforces required fields."""
    with open(dataset_schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        assert 'required' in schema, "Dataset schema must define required fields"
        required_fields = schema['required']
        assert 'discharge_id' in required_fields, "discharge_id must be required"
        assert 'data_fields' in required_fields, "data_fields must be required"

def test_output_schema_has_expected_columns_structure(output_schema_path):
    """Verify output schema structure for expected_columns."""
    with open(output_schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        for col in schema['expected_columns']:
            assert 'name' in col, "Column must have a name"
            assert 'type' in col, "Column must have a type"
            assert 'description' in col, "Column must have a description"
            assert col['type'] in ['integer', 'float', 'string', 'datetime'], f"Invalid type for {col['name']}"