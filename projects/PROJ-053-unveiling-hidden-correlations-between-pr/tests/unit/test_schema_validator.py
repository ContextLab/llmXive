import os
import csv
import tempfile
import yaml
import pytest
from pathlib import Path

from code.data.schema_validator import load_schema, validate_csv_schema, validate_and_report

@pytest.fixture
def temp_schema_file():
    """Create a temporary schema file for testing."""
    schema = {
        'required_columns': [
            {'name': 'laser_power', 'type': 'numeric'},
            {'name': 'scan_speed', 'type': 'numeric'}
        ],
        'optional_columns': [
            {'name': 'alloy_type', 'type': 'categorical'}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def valid_csv_file():
    """Create a temporary valid CSV file for testing."""
    data = [
        ['laser_power', 'scan_speed', 'alloy_type'],
        ['200', '500', 'Ti64'],
        ['300', '600', 'Inconel718']
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def invalid_csv_file():
    """Create a temporary invalid CSV file (missing required column) for testing."""
    data = [
        ['laser_power', 'alloy_type'],  # Missing scan_speed
        ['200', 'Ti64']
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def bad_type_csv_file():
    """Create a temporary CSV file with bad numeric type."""
    data = [
        ['laser_power', 'scan_speed'],
        ['200', 'invalid_speed']
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        yield f.name
    os.unlink(f.name)

def test_load_schema_success(temp_schema_file):
    """Test successful loading of a schema file."""
    schema = load_schema(temp_schema_file)
    assert 'required_columns' in schema
    assert len(schema['required_columns']) == 2
    assert schema['required_columns'][0]['name'] == 'laser_power'

def test_load_schema_not_found():
    """Test loading a non-existent schema file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent_file.yaml")

def test_validate_csv_schema_valid(valid_csv_file, temp_schema_file):
    """Test validation of a valid CSV file."""
    is_valid, errors = validate_csv_schema(valid_csv_file, load_schema(temp_schema_file))
    assert is_valid is True
    assert len(errors) == 0

def test_validate_csv_schema_missing_columns(invalid_csv_file, temp_schema_file):
    """Test validation fails when required columns are missing."""
    is_valid, errors = validate_csv_schema(invalid_csv_file, load_schema(temp_schema_file))
    assert is_valid is False
    assert len(errors) > 0
    assert "Missing required columns" in errors[0]

def test_validate_csv_schema_bad_type(bad_type_csv_file, temp_schema_file):
    """Test validation fails when numeric type is invalid."""
    is_valid, errors = validate_csv_schema(bad_type_csv_file, load_schema(temp_schema_file))
    assert is_valid is False
    assert len(errors) > 0
    assert "Invalid numeric value" in errors[0]

def test_validate_and_report_valid(valid_csv_file, temp_schema_file, capsys):
    """Test validate_and_report returns True for valid file."""
    result = validate_and_report(valid_csv_file, temp_schema_file)
    assert result is True
    captured = capsys.readouterr()
    assert "Validation PASSED" in captured.out

def test_validate_and_report_invalid(invalid_csv_file, temp_schema_file, capsys):
    """Test validate_and_report returns False for invalid file."""
    result = validate_and_report(invalid_csv_file, temp_schema_file)
    assert result is False
    captured = capsys.readouterr()
    assert "Validation FAILED" in captured.out