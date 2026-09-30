import os
import pytest
import tempfile
import csv
import yaml
from pathlib import Path

# Mock config paths for testing if necessary, or rely on real paths if setup
# For this unit test, we create temporary files.

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.schema_validator import load_schema, validate_csv_schema, validate_and_report
from config import get_contracts_dir, get_raw_data_dir, ensure_directories


def test_load_schema_valid():
    """Test loading a valid YAML schema."""
    # Create a temporary schema file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'type': 'object',
            'properties': {'col1': {'type': 'number'}},
            'required': ['col1']
        }, f)
        temp_path = f.name

    try:
        schema = load_schema(temp_path)
        assert 'required' in schema
        assert 'col1' in schema['properties']
    finally:
        os.unlink(temp_path)


def test_load_schema_missing_file():
    """Test loading a missing schema file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent_file.yaml")


def test_validate_csv_schema_missing_file():
    """Test validating a missing CSV file raises FileNotFoundError."""
    schema = {
        'type': 'object',
        'properties': {'col1': {'type': 'number'}},
        'required': ['col1']
    }
    with pytest.raises(FileNotFoundError):
        validate_csv_schema("non_existent.csv", schema)


def test_validate_csv_schema_missing_columns():
    """Test validation fails if required columns are missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['col1', 'col2']) # Missing required 'col3'
        writer.writerow(['1.0', '2.0'])
        temp_path = f.name

    try:
        schema = {
            'type': 'object',
            'properties': {'col1': {'type': 'number'}, 'col3': {'type': 'number'}},
            'required': ['col1', 'col3']
        }
        with pytest.raises(ValueError) as exc_info:
            validate_csv_schema(temp_path, schema)
        assert 'Missing required columns' in str(exc_info.value)
    finally:
        os.unlink(temp_path)


def test_validate_csv_schema_non_numeric():
    """Test validation fails if numeric column contains non-numeric data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['col1'])
        writer.writerow(['1.0'])
        writer.writerow(['not_a_number'])
        temp_path = f.name

    try:
        schema = {
            'type': 'object',
            'properties': {'col1': {'type': 'number'}},
            'required': ['col1']
        }
        with pytest.raises(ValueError) as exc_info:
            validate_csv_schema(temp_path, schema)
        assert 'non-numeric data' in str(exc_info.value)
    finally:
        os.unlink(temp_path)


def test_validate_csv_schema_valid():
    """Test validation passes for a valid CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['laser_power', 'scan_speed', 'layer_thickness'])
        writer.writerow(['200.0', '1000.0', '0.03'])
        writer.writerow(['250.5', '1200.0', '0.04'])
        temp_path = f.name

    try:
        schema = {
            'type': 'object',
            'properties': {
                'laser_power': {'type': 'number'},
                'scan_speed': {'type': 'number'},
                'layer_thickness': {'type': 'number'}
            },
            'required': ['laser_power', 'scan_speed', 'layer_thickness']
        }
        result = validate_csv_schema(temp_path, schema)
        assert result is True
    finally:
        os.unlink(temp_path)
