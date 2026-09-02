"""
Unit tests for T017a: Environmental Validation.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.validation import (
    ConfigurationError,
    load_solvent_reference,
    check_dielectric_deviation,
    validate_environmental_conditions,
    validate_solvent_series_runs,
    write_validation_report
)


@pytest.fixture
def temp_solvent_file(tmp_path):
    """Create a temporary solvents.yaml file with version_hash."""
    data = {
        "solvents": [
            {"name": "cyclohexane", "dielectric_constant": 2.02},
            {"name": "ethanol", "dielectric_constant": 24.55}
        ],
        "metadata": {
            "version_hash": "abc123def456",
            "version": "1.0.0"
        }
    }
    file_path = tmp_path / "solvents.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(data, f)
    return file_path


@pytest.fixture
def temp_env_logs(tmp_path):
    """Create a temporary environment_logs.json file."""
    data = [
        {
            "run_id": "run_001",
            "solvent_name": "cyclohexane",
            "logged_dielectric_constant": 2.03,
            "temperature_c": 25.1,
            "humidity_percent": 45.0,
            "target_humidity_percent": 45.0
        },
        {
            "run_id": "run_002",
            "solvent_name": "ethanol",
            "logged_dielectric_constant": 25.00, # Deviation > 2%
            "temperature_c": 26.0, # Deviation > 0.5
            "humidity_percent": 50.0, # Deviation > 2%
            "target_humidity_percent": 45.0
        }
    ]
    file_path = tmp_path / "environment_logs.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path


def test_check_dielectric_deviation_valid():
    """Test valid dielectric constant check."""
    is_valid, deviation = check_dielectric_deviation(2.02, 2.02)
    assert is_valid
    assert deviation == 0.0

    is_valid, deviation = check_dielectric_deviation(2.03, 2.02) # ~0.5%
    assert is_valid
    assert deviation < 2.0


def test_check_dielectric_deviation_invalid():
    """Test invalid dielectric constant check (>2%)."""
    is_valid, deviation = check_dielectric_deviation(2.10, 2.02) # ~4%
    assert not is_valid
    assert deviation > 2.0


def test_load_solvent_reference_missing_hash(temp_solvent_file):
    """Test that load_solvent_reference raises error if version_hash is missing."""
    # Modify the file to remove hash
    data = {
        "solvents": [{"name": "cyclohexane", "dielectric_constant": 2.02}],
        "metadata": {"version": "1.0.0"}
    }
    with open(temp_solvent_file, 'w') as f:
        yaml.dump(data, f)

    with patch('code.analysis.validation.get_chemicals_path') as mock_path:
        mock_path.return_value = temp_solvent_file.parent
        with pytest.raises(ConfigurationError, match="missing 'version_hash'"):
            load_solvent_reference()


def test_validate_environmental_conditions_pass():
    """Test validation of a passing run."""
    solvent_ref = {
        "solvents": [{"name": "cyclohexane", "dielectric_constant": 2.02}],
        "metadata": {"version_hash": "test"}
    }
    run_log = {
        "run_id": "run_001",
        "solvent_name": "cyclohexane",
        "logged_dielectric_constant": 2.02,
        "temperature_c": 25.0,
        "humidity_percent": 45.0,
        "target_humidity_percent": 45.0
    }

    result = validate_environmental_conditions(run_log, solvent_ref)
    assert result['is_valid']
    assert len(result['flags']) == 0


def test_validate_environmental_conditions_fail():
    """Test validation of a failing run."""
    solvent_ref = {
        "solvents": [{"name": "ethanol", "dielectric_constant": 24.55}],
        "metadata": {"version_hash": "test"}
    }
    run_log = {
        "run_id": "run_002",
        "solvent_name": "ethanol",
        "logged_dielectric_constant": 25.50, # Deviation
        "temperature_c": 26.0, # Deviation
        "humidity_percent": 50.0, # Deviation
        "target_humidity_percent": 45.0
    }

    result = validate_environmental_conditions(run_log, solvent_ref)
    assert not result['is_valid']
    assert len(result['flags']) > 0
    # Check for specific flag types
    flag_types = [f['type'] for f in result['flags']]
    assert 'dielectric_deviation' in flag_types
    assert 'temperature_out_of_tolerance' in flag_types
    assert 'humidity_out_of_tolerance' in flag_types


def test_write_validation_report(tmp_path):
    """Test writing validation report."""
    flagged_runs = [
        {"run_id": "run_002", "is_valid": False, "flags": [{"type": "test"}]}
    ]
    output_path = tmp_path / "validation_flags.json"

    write_validation_report(flagged_runs, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    assert data['total_flagged'] == 1
    assert len(data['flagged_runs']) == 1