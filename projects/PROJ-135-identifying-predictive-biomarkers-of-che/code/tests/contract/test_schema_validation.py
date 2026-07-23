"""
Contract tests for YAML schema validation.
Validates that data artifacts conform to defined schemas in specs/contracts.
"""
import os
import sys
import json
import yaml
from pathlib import Path
import pytest

# Import project config to locate paths
from src.config import ensure_directories

# Path to the contracts directory
CONTRACTS_DIR = Path("specs/001-chemo-biomarker-discovery/contracts")

def load_schema(schema_name: str) -> dict:
    """Load a schema definition from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_type(value: any, expected_type: str, field_name: str) -> None:
    """Validate that a value matches the expected type."""
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    if expected_type not in type_map:
        raise ValueError(f"Unknown type: {expected_type}")
    
    if not isinstance(value, type_map[expected_type]):
        raise TypeError(
            f"Field '{field_name}' expected type '{expected_type}', "
            f"got '{type(value).__name__}'"
        )

def validate_required_fields(data: dict, required_fields: list, schema_name: str) -> None:
    """Ensure all required fields are present in the data."""
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(
            f"Schema '{schema_name}' missing required fields: {missing}"
        )

def validate_data_against_schema(data_path: Path, schema_name: str) -> dict:
    """
    Validate a data file against its schema.
    Returns a dict with validation status and details.
    """
    if not data_path.exists():
        return {
            "status": "error",
            "message": f"Data file not found: {data_path}"
        }
    
    try:
        # Load schema
        schema = load_schema(schema_name)
        
        # Load data (support JSON or YAML)
        with open(data_path, 'r') as f:
            if data_path.suffix in ['.json']:
                data = json.load(f)
            elif data_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported file format: {data_path.suffix}"
                }
        
        # Validate required fields
        required_fields = schema.get('required', [])
        validate_required_fields(data, required_fields, schema_name)
        
        # Validate types for each field
        properties = schema.get('properties', {})
        for field, expected_type in properties.items():
            if field in data:
                validate_type(data[field], expected_type, field)
        
        return {
            "status": "valid",
            "schema": schema_name,
            "file": str(data_path)
        }
        
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        return {
            "status": "error",
            "message": f"Failed to parse data file: {str(e)}"
        }
    except (ValueError, TypeError, FileNotFoundError) as e:
        return {
            "status": "invalid",
            "message": str(e)
        }

# --- Test Cases ---

def test_schemas_exist():
    """Verify that all expected schema files exist."""
    expected_schemas = [
        'dataset.schema.yaml',
        'model_output.schema.yaml',
        'meta_analysis.schema.yaml'
    ]
    
    for schema in expected_schemas:
        schema_path = CONTRACTS_DIR / schema
        assert schema_path.exists(), f"Missing schema file: {schema_path}"

def test_schemas_load_valid_yaml():
    """Verify that schema files are valid YAML."""
    for schema_file in CONTRACTS_DIR.glob("*.schema.yaml"):
        try:
            with open(schema_file, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {schema_file}: {e}")

def test_dataset_schema_structure():
    """Verify the dataset schema has the expected structure."""
    schema = load_schema('dataset.schema.yaml')
    
    assert 'properties' in schema
    assert 'required' in schema
    
    # Check for key fields expected in dataset schema
    expected_fields = ['tumor_type', 'sample_id', 'gene_expression', 'response_label']
    for field in expected_fields:
        assert field in schema['properties'], f"Missing field in dataset schema: {field}"

def test_model_output_schema_structure():
    """Verify the model output schema has the expected structure."""
    schema = load_schema('model_output.schema.yaml')
    
    assert 'properties' in schema
    assert 'required' in schema
    
    expected_fields = ['model_id', 'tumor_type', 'metrics', 'coefficients']
    for field in expected_fields:
        assert field in schema['properties'], f"Missing field in model schema: {field}"

def test_meta_analysis_schema_structure():
    """Verify the meta-analysis schema has the expected structure."""
    schema = load_schema('meta_analysis.schema.yaml')
    
    assert 'properties' in schema
    assert 'required' in schema
    
    expected_fields = ['gene_panel', 'stouffer_pvalues', 'method']
    for field in expected_fields:
        assert field in schema['properties'], f"Missing field in meta-analysis schema: {field}"

def test_sample_data_validation(tmp_path):
    """Test validation logic with a sample valid data file."""
    # Create a sample valid JSON file
    sample_data = {
        "tumor_type": "BRCA",
        "sample_id": "TCGA-AB-1234",
        "gene_expression": {"BRCA1": 10.5, "TP53": 8.2},
        "response_label": "responder"
    }
    
    test_file = tmp_path / "sample_dataset.json"
    with open(test_file, 'w') as f:
        json.dump(sample_data, f)
    
    result = validate_data_against_schema(test_file, 'dataset.schema.yaml')
    
    assert result['status'] == 'valid', f"Validation failed: {result.get('message')}"

def test_invalid_data_catches_error(tmp_path):
    """Test that validation catches missing required fields."""
    # Create a sample invalid JSON file (missing required field)
    invalid_data = {
        "tumor_type": "BRCA",
        "gene_expression": {"BRCA1": 10.5}
        # Missing: sample_id, response_label
    }
    
    test_file = tmp_path / "invalid_dataset.json"
    with open(test_file, 'w') as f:
        json.dump(invalid_data, f)
    
    result = validate_data_against_schema(test_file, 'dataset.schema.yaml')
    
    assert result['status'] == 'invalid', "Validation should have caught missing fields"
    assert 'missing required fields' in result['message'].lower()