"""
Unit tests for schema validator.
"""
import pytest
import csv
import yaml
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.schema_validator import (
    load_schema,
    validate_csv_schema,
    validate_and_report,
    main
)
from code.config import get_project_root


@pytest.fixture
def sample_schema():
    """Create a temporary schema file for testing."""
    schema = {
        'required': ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility'],
        'optional': ['fatigue_life', 'alloy_type'],
        'types': {
            'laser_power': 'float',
            'scan_speed': 'float',
            'layer_thickness': 'float',
            'yield_strength': 'float',
            'ductility': 'float',
            'fatigue_life': 'float',
            'alloy_type': 'str'
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def valid_csv():
    """Create a temporary valid CSV file."""
    data = [
        ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility'],
        ['200.0', '500.0', '0.03', '450.5', '12.3'],
        ['250.0', '600.0', '0.04', '480.2', '15.1'],
        ['300.0', '700.0', '0.035', '510.8', '18.7']
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerows(data)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def invalid_csv_missing_column():
    """Create a temporary CSV with missing required column."""
    data = [
        ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength'],  # Missing ductility
        ['200.0', '500.0', '0.03', '450.5'],
        ['250.0', '600.0', '0.04', '480.2']
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerows(data)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def invalid_csv_wrong_type():
    """Create a temporary CSV with wrong data type."""
    data = [
        ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility'],
        ['200.0', 'invalid_speed', '0.03', '450.5', '12.3'],  # scan_speed is not float
        ['250.0', '600.0', '0.04', '480.2', '15.1']
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerows(data)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


def test_load_schema_valid(sample_schema):
    """Test loading a valid schema file."""
    schema = load_schema(sample_schema)
    
    assert 'required' in schema
    assert 'optional' in schema
    assert 'types' in schema
    assert len(schema['required']) == 5
    assert 'fatigue_life' in schema['optional']


def test_load_schema_missing_file():
    """Test loading a non-existent schema file."""
    with pytest.raises(FileNotFoundError):
        load_schema('/nonexistent/path/schema.yaml')


def test_validate_csv_schema_valid(valid_csv, sample_schema):
    """Test validation of a valid CSV file."""
    schema = load_schema(sample_schema)
    is_valid, errors = validate_csv_schema(valid_csv, schema)
    
    assert is_valid
    assert len(errors) == 0


def test_validate_csv_schema_missing_column(invalid_csv_missing_column, sample_schema):
    """Test validation of CSV with missing required column."""
    schema = load_schema(sample_schema)
    is_valid, errors = validate_csv_schema(invalid_csv_missing_column, schema)
    
    assert not is_valid
    assert len(errors) > 0
    assert any('ductility' in error for error in errors)


def test_validate_csv_schema_wrong_type(invalid_csv_wrong_type, sample_schema):
    """Test validation of CSV with wrong data type."""
    schema = load_schema(sample_schema)
    is_valid, errors = validate_csv_schema(invalid_csv_wrong_type, schema)
    
    assert not is_valid
    assert len(errors) > 0
    assert any('scan_speed' in error for error in errors)


def test_validate_csv_schema_nonexistent_file():
    """Test validation of non-existent CSV file."""
    schema = load_schema('/nonexistent/schema.yaml')
    
    with pytest.raises(FileNotFoundError):
        validate_csv_schema('/nonexistent/file.csv', schema)


def test_validate_and_report_valid(valid_csv, sample_schema, capsys):
    """Test validate_and_report with valid CSV."""
    result = validate_and_report(valid_csv, sample_schema)
    
    assert result is True
    captured = capsys.readouterr()
    assert 'PASSED' in captured.out


def test_validate_and_report_invalid(invalid_csv_missing_column, sample_schema, capsys):
    """Test validate_and_report with invalid CSV."""
    result = validate_and_report(invalid_csv_missing_column, sample_schema)
    
    assert result is False
    captured = capsys.readouterr()
    assert 'FAILED' in captured.out
    assert 'ductility' in captured.out
