"""
Unit tests for validate_eeg_fields.py
"""
import pytest
import tempfile
import os
from pathlib import Path
import csv
import json

# Import the functions to test
# Note: We import the module directly to test internal functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from validate_eeg_fields import validate_fields, load_raw_data

def test_validate_fields_all_present():
    """Test validation when all required fields are present."""
    data = [
        {'age': 25, 'sex': 'M', 'bmi': 22.5},
        {'age': 30, 'sex': 'F', 'bmi': 24.0}
    ]
    required = ['age', 'sex', 'bmi']
    optional = ['diet']
    
    result = validate_fields(data, required, optional)
    
    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert result['total_records'] == 2

def test_validate_fields_missing_required():
    """Test validation when a required field is missing."""
    data = [
        {'age': 25, 'sex': 'M'}, # missing bmi
        {'age': 30, 'sex': 'F', 'bmi': 24.0}
    ]
    required = ['age', 'sex', 'bmi']
    optional = ['diet']
    
    result = validate_fields(data, required, optional)
    
    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'Missing required field' in result['errors'][0]
    assert result['missing_counts']['bmi'] == 1

def test_validate_fields_empty_value():
    """Test validation when a required field has an empty value."""
    data = [
        {'age': 25, 'sex': '', 'bmi': 22.5},
        {'age': 30, 'sex': 'F', 'bmi': 24.0}
    ]
    required = ['age', 'sex', 'bmi']
    optional = ['diet']
    
    result = validate_fields(data, required, optional)
    
    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'empty' in result['errors'][0]

def test_validate_fields_optional_missing():
    """Test validation when optional field is missing (should be valid)."""
    data = [
        {'age': 25, 'sex': 'M', 'bmi': 22.5},
        {'age': 30, 'sex': 'F', 'bmi': 24.0}
    ]
    required = ['age', 'sex', 'bmi']
    optional = ['diet'] # diet is missing in both, which is fine for OpenNeuro
    
    result = validate_fields(data, required, optional)
    
    assert result['valid'] is True
    assert len(result['errors']) == 0

def test_load_raw_data_csv(tmp_path):
    """Test loading raw data from a CSV file."""
    csv_file = tmp_path / "test_data.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['age', 'sex', 'bmi'])
        writer.writeheader()
        writer.writerow({'age': 25, 'sex': 'M', 'bmi': 22.5})
        writer.writerow({'age': 30, 'sex': 'F', 'bmi': 24.0})
    
    data = load_raw_data(csv_file)
    
    assert len(data) == 2
    assert data[0]['age'] == 25
    assert data[1]['sex'] == 'F'

def test_load_raw_data_file_not_found():
    """Test loading raw data when file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_raw_data(Path("/nonexistent/path/file.csv"))
