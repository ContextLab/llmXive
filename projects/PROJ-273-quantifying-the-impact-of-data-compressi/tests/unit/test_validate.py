import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.validate import check_true_parameters_exist, validate_metadata, validate_file


@pytest.fixture
def valid_metadata_with_true_params():
    """Create a temporary metadata file containing true_parameters."""
    data = {
        "event_id": "GW150914",
        "detector": "LIGO-H1",
        "timestamp": 1126259462,
        "true_parameters": {
            "mass_1": 36.0,
            "mass_2": 29.0,
            "distance": 410.0,
            "spin_1": {"tilt": 0.5, "azimuth": 1.2},
            "spin_2": {"tilt": 0.1, "azimuth": 2.5}
        },
        "snr": 24.5
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def metadata_missing_true_params():
    """Create a temporary metadata file missing true_parameters."""
    data = {
        "event_id": "GW150914",
        "detector": "LIGO-H1",
        "timestamp": 1126259462,
        "snr": 24.5
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


def test_validate_metadata_contains_true_parameters(valid_metadata_with_true_params):
    """Test that validate_metadata returns True when true_parameters exist."""
    with open(valid_metadata_with_true_params, 'r') as f:
        metadata = json.load(f)
    
    result = validate_metadata(metadata)
    
    assert result is True, "validate_metadata should return True when true_parameters are present"
    assert 'true_parameters' in metadata


def test_validate_metadata_missing_true_parameters(metadata_missing_true_params):
    """Test that validate_metadata returns False when true_parameters are missing."""
    with open(metadata_missing_true_params, 'r') as f:
        metadata = json.load(f)
    
    result = validate_metadata(metadata)
    
    assert result is False, "validate_metadata should return False when true_parameters are missing"
    assert 'true_parameters' not in metadata


def test_check_true_parameters_exist(valid_metadata_with_true_params):
    """Test check_true_parameters_exist with valid file."""
    exists = check_true_parameters_exist(valid_metadata_with_true_params)
    assert exists is True, "check_true_parameters_exist should return True for valid file"


def test_check_true_parameters_missing(metadata_missing_true_params):
    """Test check_true_parameters_exist with file missing true_parameters."""
    exists = check_true_parameters_exist(metadata_missing_true_params)
    assert exists is False, "check_true_parameters_exist should return False when true_parameters missing"


def test_check_true_parameters_file_not_found():
    """Test check_true_parameters_exist with non-existent file."""
    exists = check_true_parameters_exist("non_existent_file.json")
    assert exists is False, "check_true_parameters_exist should return False for missing file"


def test_validate_file_integration(valid_metadata_with_true_params):
    """Integration test for validate_file with valid metadata."""
    is_valid, msg = validate_file(valid_metadata_with_true_params)
    assert is_valid is True, f"validate_file should pass for valid file: {msg}"


def test_validate_file_integration_missing(metadata_missing_true_params):
    """Integration test for validate_file with missing true_parameters."""
    is_valid, msg = validate_file(metadata_missing_true_params)
    assert is_valid is False, f"validate_file should fail for missing true_parameters: {msg}"
    assert "true_parameters" in msg
