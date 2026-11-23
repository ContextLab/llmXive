"""
Unit tests for validation utilities.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
import yaml
from code.validators import (
    validate_smiles,
    check_target_range,
    load_schema,
    validate_csv_against_schema,
    validate_json_against_schema,
    validate_file
)

def test_validate_smiles_valid():
    """Test validation of valid SMILES strings"""
    valid_smiles = ["CCO", "c1ccccc1", "CC(=O)O"]
    for smiles in valid_smiles:
        is_valid, error = validate_smiles(smiles)
        assert is_valid, f"Expected {smiles} to be valid, got error: {error}"
        assert error is None

def test_validate_smiles_invalid():
    """Test validation of invalid SMILES strings"""
    invalid_smiles = ["", "invalid", "C((", "123"]
    for smiles in invalid_smiles:
        is_valid, error = validate_smiles(smiles)
        assert not is_valid, f"Expected {smiles} to be invalid"
        assert error is not None

def test_check_target_range_sufficient():
    """Test target range check with sufficient range"""
    values = pd.Series([1e-6, 1e-3, 1e0, 1e3, 1e6])
    assert check_target_range(values, min_log_range=3.0) is True

def test_check_target_range_insufficient():
    """Test target range check with insufficient range"""
    values = pd.Series([1e-1, 1e0, 1e1])  # Range of 2 orders of magnitude
    assert check_target_range(values, min_log_range=3.0) is False

def test_check_target_range_empty():
    """Test target range check with empty series"""
    values = pd.Series([])
    assert check_target_range(values, min_log_range=3.0) is False

def test_validate_csv_against_schema():
    """Test CSV validation against schema"""
    # Create a simple schema
    schema = {
        'required_columns': ['name', 'value'],
        'column_types': {
            'name': 'string',
            'value': 'numeric'
        }
    }
    
    # Valid DataFrame
    df_valid = pd.DataFrame({
        'name': ['a', 'b', 'c'],
        'value': [1.0, 2.0, 3.0]
    })
    is_valid, errors = validate_csv_against_schema(df_valid, schema)
    assert is_valid is True
    assert len(errors) == 0
    
    # Invalid DataFrame - missing column
    df_missing = pd.DataFrame({
        'name': ['a', 'b'],
    })
    is_valid, errors = validate_csv_against_schema(df_missing, schema)
    assert is_valid is False
    assert 'Missing required columns' in errors[0]
    
    # Invalid DataFrame - wrong type
    df_wrong_type = pd.DataFrame({
        'name': ['a', 'b'],
        'value': ['x', 'y']
    })
    is_valid, errors = validate_csv_against_schema(df_wrong_type, schema)
    assert is_valid is False
    assert any('should be numeric' in err for err in errors)

def test_validate_json_against_schema():
    """Test JSON validation against schema"""
    schema = {
        'required_fields': ['id', 'name'],
        'field_types': {
            'id': 'number',
            'name': 'string',
            'tags': 'array'
        }
    }
    
    # Valid data
    data_valid = {
        'id': 1,
        'name': 'test',
        'tags': ['a', 'b']
    }
    is_valid, errors = validate_json_against_schema(data_valid, schema)
    assert is_valid is True
    assert len(errors) == 0
    
    # Invalid data - missing field
    data_missing = {
        'id': 1,
        'tags': ['a']
    }
    is_valid, errors = validate_json_against_schema(data_missing, schema)
    assert is_valid is False
    assert 'Missing required fields' in errors[0]
    
    # Invalid data - wrong type
    data_wrong_type = {
        'id': 'not_a_number',
        'name': 'test'
    }
    is_valid, errors = validate_json_against_schema(data_wrong_type, schema)
    assert is_valid is False
    assert any('should be a number' in err for err in errors)

def test_validate_file_csv():
    """Test file validation for CSV"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create schema
        schema = {
            'required_columns': ['col1'],
            'column_types': {'col1': 'numeric'}
        }
        schema_path = os.path.join(tmpdir, 'schema.yaml')
        with open(schema_path, 'w') as f:
            yaml.dump(schema, f)
        
        # Create valid CSV
        df = pd.DataFrame({'col1': [1, 2, 3]})
        csv_path = os.path.join(tmpdir, 'data.csv')
        df.to_csv(csv_path, index=False)
        
        is_valid, errors = validate_file(csv_path, schema_path)
        assert is_valid is True
        assert len(errors) == 0

def test_validate_file_json():
    """Test file validation for JSON"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create schema
        schema = {
            'required_fields': ['key'],
            'field_types': {'key': 'string'}
        }
        schema_path = os.path.join(tmpdir, 'schema.yaml')
        with open(schema_path, 'w') as f:
            yaml.dump(schema, f)
        
        # Create valid JSON
        data = {'key': 'value'}
        json_path = os.path.join(tmpdir, 'data.json')
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        is_valid, errors = validate_file(json_path, schema_path)
        assert is_valid is True
        assert len(errors) == 0

def test_validate_file_not_found():
    """Test file validation with non-existent file"""
    is_valid, errors = validate_file('nonexistent.csv', 'nonexistent.yaml')
    assert is_valid is False
    assert 'not found' in errors[0].lower()