"""
Unit test for T004c: Aggregated Metric Schema Definition and Validation.
Verifies that the schema file exists, is valid YAML, and conforms to the expected structure.
"""
import os
import json
import pytest
import yaml
from pathlib import Path

# Project root
project_root = Path(__file__).resolve().parent.parent.parent
schema_path = project_root / "specs" / "001-assess-heterogeneity-impact" / "contracts" / "aggregated_metric.schema.yaml"

def test_schema_file_exists():
    """Verify the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_schema_is_valid_yaml():
    """Verify the schema file is valid YAML."""
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert schema is not None, "Schema loaded as None"
    except yaml.YAMLError as e:
        pytest.fail(f"Schema is not valid YAML: {e}")

def test_schema_has_required_structure():
    """Verify the schema contains the required keys and structure."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    assert 'type' in schema, "Schema missing 'type'"
    assert schema['type'] == 'object', "Schema type must be 'object'"
    
    assert 'required' in schema, "Schema missing 'required' list"
    required_fields = schema['required']
    
    # Check specific required fields from T004c spec
    expected_fields = [
        'tau2_level',
        'coverage_rate',
        'mean_bias',
        'p_value_binomial',
        'p_value_normality_test',
        'test_type_bias_comparison'
    ]
    
    for field in expected_fields:
        assert field in required_fields, f"Required field '{field}' missing from schema"
    
    assert 'properties' in schema, "Schema missing 'properties'"
    properties = schema['properties']
    
    for field in expected_fields:
        assert field in properties, f"Property '{field}' missing from schema properties"

def test_schema_validates_dummy_record():
    """Verify the schema validates a valid dummy record."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    dummy_record = {
        "tau2_level": 0.5,
        "coverage_rate": 0.95,
        "mean_bias": 0.01,
        "p_value_binomial": 0.4,
        "p_value_normality_test": 0.6,
        "test_type_bias_comparison": "ANOVA"
    }

    try:
        import jsonschema
        jsonschema.validate(instance=dummy_record, schema=schema)
    except ImportError:
        # Manual check if jsonschema not available
        required = schema.get('required', [])
        props = schema.get('properties', {})
        for key, value in dummy_record.items():
            assert key in required or key in props, f"Key {key} not in schema"
            # Basic type check
            if props.get(key, {}).get('type') == 'number':
                assert isinstance(value, (int, float)), f"{key} should be number"
            elif props.get(key, {}).get('type') == 'string':
                assert isinstance(value, str), f"{key} should be string"

def test_schema_rejects_invalid_record():
    """Verify the schema rejects a record with missing required fields."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    invalid_record = {
        "tau2_level": 0.5,
        # Missing coverage_rate and others
    }

    try:
        import jsonschema
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_record, schema=schema)
    except ImportError:
        # Manual check
        required = schema.get('required', [])
        for field in required:
            if field not in invalid_record:
                # Expected to fail
                return
        pytest.fail("Schema should have rejected invalid record")