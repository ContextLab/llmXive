"""
Unit tests for code/analysis/validation.py (T017).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Import the module under test
from analysis.validation import (
    load_solvent_reference,
    check_dielectric_deviation,
    validate_solvent_series_runs,
    calculate_environmental_compliance,
    ConfigurationError
)
from config import get_chemicals_path, get_processed_data_path

@pytest.fixture
def mock_solvents_yaml(tmp_path):
    """Create a temporary solvents.yaml with valid version_hash."""
    data = {
        'solvents': [
            {'name': 'cyclohexane', 'dielectric_constant': 2.02},
            {'name': 'ethanol', 'dielectric_constant': 24.55}
        ],
        'metadata': {
            'version': '1.0.0',
            'version_hash': 'abc123xyz'
        }
    }
    file_path = tmp_path / 'solvents.yaml'
    with open(file_path, 'w') as f:
        yaml.dump(data, f)
    return file_path

@pytest.fixture
def mock_env_logs(tmp_path):
    """Create a temporary environment_logs.json."""
    data = [
        {
            'run_id': 'run_001',
            'solvent_name': 'cyclohexane',
            'dielectric_constant': 2.02,
            'temperature_c': 25.0,
            'relative_humidity_pct': 50.0,
            'n': 1
        },
        {
            'run_id': 'run_002',
            'solvent_name': 'ethanol',
            'dielectric_constant': 24.55,
            'temperature_c': 25.0,
            'relative_humidity_pct': 50.0,
            'n': 1
        }
    ]
    file_path = tmp_path / 'environment_logs.json'
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_load_solvent_reference_success(mock_solvents_yaml):
    """Test successful loading of solvent reference."""
    with patch('analysis.validation.get_chemicals_path') as mock_get_path:
        mock_get_path.return_value = mock_solvents_yaml.parent
        result = load_solvent_reference()
        assert 'cyclohexane' in result
        assert result['cyclohexane'] == 2.02
        assert 'ethanol' in result

def test_load_solvent_reference_missing_file(tmp_path):
    """Test ConfigurationError when solvents.yaml is missing."""
    with patch('analysis.validation.get_chemicals_path') as mock_get_path:
        mock_get_path.return_value = tmp_path
        with pytest.raises(ConfigurationError) as exc_info:
            load_solvent_reference()
        assert "does not exist" in str(exc_info.value)

def test_load_solvent_reference_missing_hash(mock_solvents_yaml):
    """Test ConfigurationError when version_hash is missing."""
    data = {
        'solvents': [{'name': 'test', 'dielectric_constant': 1.0}],
        'metadata': {'version': '1.0.0'}
    }
    file_path = mock_solvents_yaml.parent / 'solvents_no_hash.yaml'
    with open(file_path, 'w') as f:
        yaml.dump(data, f)

    with patch('analysis.validation.get_chemicals_path') as mock_get_path:
        mock_get_path.return_value = file_path.parent
        # Patch the filename check to use our new file
        with patch('analysis.validation.Path.__truediv__', return_value=file_path):
            with pytest.raises(ConfigurationError) as exc_info:
                load_solvent_reference()
            assert "version_hash" in str(exc_info.value)

def test_check_dielectric_deviation_within_tolerance():
    """Test deviation calculation within 2%."""
    is_valid, deviation = check_dielectric_deviation('test', 2.04, 2.00)
    assert is_valid
    assert abs(deviation - 2.0) < 0.01

def test_check_dielectric_deviation_exceeds_tolerance():
    """Test deviation calculation exceeding 2%."""
    is_valid, deviation = check_dielectric_deviation('test', 2.10, 2.00)
    assert not is_valid
    assert deviation > 2.0

def test_validate_solvent_series_runs():
    """Test validation logic for solvent series."""
    reference = {'cyclohexane': 2.02, 'ethanol': 24.55}
    logs = [
        {'run_id': 'r1', 'solvent_name': 'cyclohexane', 'dielectric_constant': 2.02},
        {'run_id': 'r2', 'solvent_name': 'ethanol', 'dielectric_constant': 25.00} # Deviation
    ]

    results = validate_solvent_series_runs(logs, reference)

    assert len(results) == 2
    assert results[0]['dielectric_valid'] is True
    assert results[1]['dielectric_valid'] is False
    assert results[1]['reason'] is not None

def test_calculate_environmental_compliance():
    """Test compliance percentage calculation."""
    logs = [
        {'run_id': 'r1', 'temperature_c': 25.0, 'relative_humidity_pct': 50.0, 'n': 1},
        {'run_id': 'r2', 'temperature_c': 25.0, 'relative_humidity_pct': 50.0, 'n': 1}
    ]
    validation_results = [
        {'dielectric_valid': True},
        {'dielectric_valid': True}
    ]

    compliance = calculate_environmental_compliance(logs, validation_results, 2)

    assert compliance['compliance_percentage'] == 100.0
    assert compliance['meets_target'] is True
    assert compliance['compliant_runs'] == 2

def test_calculate_environmental_compliance_failures():
    """Test compliance with failures."""
    logs = [
        {'run_id': 'r1', 'temperature_c': 25.0, 'relative_humidity_pct': 50.0, 'n': 1},
        {'run_id': 'r2', 'temperature_c': 30.0, 'relative_humidity_pct': 50.0, 'n': 1} # Temp fail
    ]
    validation_results = [
        {'dielectric_valid': True},
        {'dielectric_valid': True}
    ]

    compliance = calculate_environmental_compliance(logs, validation_results, 2)

    assert compliance['compliance_percentage'] == 50.0
    assert compliance['meets_target'] is False
    assert len(compliance['failures']) == 1
    assert 'Temperature' in compliance['failures'][0]['reasons'][0]
