import pytest
import pandas as pd
import tempfile
import os
import yaml
import json

# Import from the project's data module
from data.schema_validator import (
    load_schema,
    validate_csv_schema,
    validate_and_report
)

@pytest.fixture
def sample_schema():
    """Create a sample schema for testing."""
    return {
        'required_columns': ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility'],
        'optional_columns': ['fatigue_life'],
        'column_types': {
            'laser_power': 'numeric',
            'scan_speed': 'numeric',
            'layer_thickness': 'numeric',
            'alloy_type': 'categorical',
            'yield_strength': 'numeric',
            'ductility': 'numeric',
            'fatigue_life': 'numeric'
        }
    }

@pytest.fixture
def valid_csv(sample_schema):
    """Create a valid CSV file."""
    data = {
        'laser_power': [200.0, 250.0, 300.0],
        'scan_speed': [500.0, 600.0, 700.0],
        'layer_thickness': [0.03, 0.04, 0.05],
        'alloy_type': ['AlSi10Mg', 'Inconel625', 'Ti64'],
        'yield_strength': [300.0, 450.0, 800.0],
        'ductility': [15.0, 25.0, 8.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    return temp_path

@pytest.fixture
def invalid_csv_missing_column():
    """Create a CSV file missing a required column."""
    data = {
        'laser_power': [200.0, 250.0, 300.0],
        'scan_speed': [500.0, 600.0, 700.0],
        'layer_thickness': [0.03, 0.04, 0.05],
        'alloy_type': ['AlSi10Mg', 'Inconel625', 'Ti64'],
        'yield_strength': [300.0, 450.0, 800.0]
        # Missing 'ductility'
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    return temp_path

@pytest.fixture
def schema_file(sample_schema):
    """Create a temporary schema YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        yaml.dump(sample_schema, f)
        temp_path = f.name
    
    return temp_path

def test_load_schema(schema_file):
    """Test loading schema from YAML file."""
    schema = load_schema(schema_file)
    
    assert schema is not None
    assert 'required_columns' in schema
    assert 'optional_columns' in schema
    assert 'column_types' in schema
    
    os.unlink(schema_file)

def test_validate_csv_schema_valid(valid_csv, schema_file):
    """Test validation of a valid CSV against schema."""
    is_valid, errors = validate_csv_schema(valid_csv, schema_file)
    
    assert is_valid
    assert len(errors) == 0
    
    os.unlink(schema_file)

def test_validate_csv_schema_invalid(valid_csv, invalid_csv_missing_column, schema_file):
    """Test validation of an invalid CSV (missing column)."""
    is_valid, errors = validate_csv_schema(invalid_csv_missing_column, schema_file)
    
    assert not is_valid
    assert len(errors) > 0
    assert any('ductility' in str(error) for error in errors)
    
    os.unlink(schema_file)

def test_validate_and_report(valid_csv, schema_file):
    """Test full validation with reporting."""
    result = validate_and_report(valid_csv, schema_file)
    
    assert result is not None
    assert 'valid' in result
    assert 'errors' in result
    assert 'warnings' in result
    
    os.unlink(schema_file)

def test_validate_and_report_invalid(invalid_csv_missing_column, schema_file):
    """Test full validation with reporting on invalid CSV."""
    result = validate_and_report(invalid_csv_missing_column, schema_file)
    
    assert result is not None
    assert result['valid'] == False
    assert len(result['errors']) > 0
    
    os.unlink(schema_file)

def test_schema_with_optional_columns(valid_csv, schema_file):
    """Test schema validation with optional columns."""
    # Add optional column to data
    data = {
        'laser_power': [200.0, 250.0, 300.0],
        'scan_speed': [500.0, 600.0, 700.0],
        'layer_thickness': [0.03, 0.04, 0.05],
        'alloy_type': ['AlSi10Mg', 'Inconel625', 'Ti64'],
        'yield_strength': [300.0, 450.0, 800.0],
        'ductility': [15.0, 25.0, 8.0],
        'fatigue_life': [1000.0, 2000.0, 1500.0]  # Optional column
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    is_valid, errors = validate_csv_schema(temp_path, schema_file)
    
    assert is_valid
    assert len(errors) == 0
    
    os.unlink(temp_path)
    os.unlink(schema_file)
