import pytest
import yaml
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from research.validate_schema import (
    load_yaml_schema,
    validate_schema_structure,
    validate_with_jsonschema,
    run_yamllint
)

@pytest.fixture
def sample_valid_schema():
    return {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'type': 'object',
        'properties': {
            'field1': {'type': 'string'},
            'field2': {'type': 'number'}
        },
        'required': ['field1']
    }

@pytest.fixture
def sample_invalid_schema():
    return {
        'type': 'object',  # Missing $schema
        'properties': {}
    }

class TestLoadYamlSchema:
    def test_load_valid_yaml(self, tmp_path):
        schema_file = tmp_path / 'test_schema.yaml'
        schema_content = {
            'type': 'object',
            'properties': {'test': {'type': 'string'}}
        }
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        result = load_yaml_schema(schema_file)
        assert result == schema_content
    
    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_yaml_schema(tmp_path / 'nonexistent.yaml')
    
    def test_load_empty_file(self, tmp_path):
        schema_file = tmp_path / 'empty.yaml'
        schema_file.touch()
        
        with pytest.raises(ValueError):
            load_yaml_schema(schema_file)

class TestValidateSchemaStructure:
    def test_valid_schema(self, sample_valid_schema):
        errors = validate_schema_structure(sample_valid_schema)
        assert len(errors) == 0
    
    def test_missing_schema_field(self, sample_invalid_schema):
        errors = validate_schema_structure(sample_invalid_schema)
        assert any('Missing' in e and '$schema' in e for e in errors)
    
    def test_missing_type_field(self):
        schema = {'properties': {}}
        errors = validate_schema_structure(schema)
        assert any('Missing' in e and 'type' in e for e in errors)
    
    def test_missing_properties_field(self):
        schema = {'type': 'object'}
        errors = validate_schema_structure(schema)
        assert any('Missing' in e and 'properties' in e for e in errors)

class TestValidateWithJsonschema:
    def test_valid_schema_syntax(self, sample_valid_schema):
        errors = validate_with_jsonschema(sample_valid_schema)
        assert len(errors) == 0
    
    def test_invalid_schema_syntax(self):
        # Invalid JSON Schema: 'type' must be a string, not a list
        invalid_schema = {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'type': ['object', 'string'],  # Invalid
            'properties': {}
        }
        errors = validate_with_jsonschema(invalid_schema)
        assert len(errors) > 0
        assert any('syntax' in e.lower() for e in errors)
    
    def test_data_validation_success(self, sample_valid_schema):
        sample_data = {'field1': 'test'}
        errors = validate_with_jsonschema(sample_valid_schema, sample_data)
        assert len(errors) == 0
    
    def test_data_validation_failure(self, sample_valid_schema):
        # Missing required field
        sample_data = {'field2': 123}
        errors = validate_with_jsonschema(sample_valid_schema, sample_data)
        assert len(errors) > 0
        assert any('required' in e.lower() for e in errors)

class TestRunYamllint:
    def test_yamllint_installed(self, tmp_path):
        # Create a valid YAML file
        yaml_file = tmp_path / 'test.yaml'
        yaml_file.write_text('key: value\n')
        
        success, msg = run_yamllint(yaml_file)
        # If yamllint is installed, it should pass
        # If not installed, it should return False with appropriate message
        if success:
            assert 'passed' in msg
        else:
            assert 'not installed' in msg or 'issues' in msg

class TestIntegration:
    def test_full_schema_validation(self, tmp_path):
        # Create a complete valid schema
        schema = {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'type': 'object',
            'properties': {
                'sample_id': {'type': 'string'},
                'InChIKey': {'type': 'string'},
                'normalized_intensity': {'type': 'number'},
                'study_id': {'type': 'string'}
            },
            'required': ['sample_id', 'InChIKey', 'normalized_intensity']
        }
        
        schema_file = tmp_path / 'test_schema.yaml'
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
        
        loaded = load_yaml_schema(schema_file)
        structure_errors = validate_schema_structure(loaded)
        jsonschema_errors = validate_with_jsonschema(loaded)
        
        assert len(structure_errors) == 0
        assert len(jsonschema_errors) == 0