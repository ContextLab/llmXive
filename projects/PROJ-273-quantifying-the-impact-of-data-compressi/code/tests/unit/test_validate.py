"""
Unit tests for src/data/validate.py
Specifically tests the requirement that 'true_parameters' exists in metadata.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path

# Add code to path if not already done by conftest
import sys
from pathlib import Path
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.validate import validate_metadata, validate_file, check_true_parameters_exist

@pytest.fixture
def valid_metadata_with_true_params():
    """Fixture providing valid metadata containing true_parameters."""
    return {
        'true_parameters': {
            'mass_1': 30.0,
            'mass_2': 20.0,
            'spin_1': 0.1,
            'tilt_angle': 0.5,
            'distance': 400.0
        },
        'strain_time_series': [0.1, 0.2, 0.3],
        'detector_name': 'LIGO_Hanford',
        'event_timestamp': 1234567890.0
    }

@pytest.fixture
def metadata_missing_true_params():
    """Fixture providing metadata missing true_parameters."""
    return {
        'strain_time_series': [0.1, 0.2, 0.3],
        'detector_name': 'LIGO_Hanford',
        'event_timestamp': 1234567890.0
    }

def test_validate_metadata_contains_true_parameters(valid_metadata_with_true_params):
    """
    Test that validate_metadata returns True when 'true_parameters' is present.
    This directly satisfies the T010 requirement: assert 'true_parameters' in metadata.
    """
    is_valid, missing = validate_metadata(valid_metadata_with_true_params)
    assert is_valid is True
    assert 'true_parameters' not in missing
    assert 'true_parameters' in valid_metadata_with_true_params

def test_validate_metadata_missing_true_parameters(metadata_missing_true_params):
    """
    Test that validate_metadata returns False and lists 'true_parameters' as missing.
    """
    is_valid, missing = validate_metadata(metadata_missing_true_params)
    assert is_valid is False
    assert 'true_parameters' in missing

def test_check_true_parameters_exist(tmp_path):
    """
    Test the helper function check_true_parameters_exist with a real file.
    """
    # Create a valid JSON file
    valid_file = tmp_path / "valid.json"
    valid_data = {
        'true_parameters': {'mass': 10.0},
        'other': 'data'
    }
    with open(valid_file, 'w') as f:
        json.dump(valid_data, f)

    assert check_true_parameters_exist(valid_file) is True

def test_check_true_parameters_missing(tmp_path):
    """
    Test the helper function check_true_parameters_exist with a file missing the key.
    """
    # Create an invalid JSON file (missing true_parameters)
    invalid_file = tmp_path / "invalid.json"
    invalid_data = {
        'some_other_key': 'value'
    }
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)

    assert check_true_parameters_exist(invalid_file) is False

def test_check_true_parameters_file_not_found(tmp_path):
    """
    Test the helper function when file does not exist.
    """
    non_existent = tmp_path / "does_not_exist.json"
    assert check_true_parameters_exist(non_existent) is False

def test_validate_file_integration(tmp_path, valid_metadata_with_true_params):
    """
    Integration test for validate_file with a valid file.
    """
    test_file = tmp_path / "test_event.json"
    with open(test_file, 'w') as f:
        json.dump(valid_metadata_with_true_params, f)
    
    is_valid, report = validate_file(test_file)
    
    assert is_valid is True
    assert report['file_exists'] is True
    assert 'true_parameters' in report['metadata']
    assert len(report['missing_fields']) == 0
