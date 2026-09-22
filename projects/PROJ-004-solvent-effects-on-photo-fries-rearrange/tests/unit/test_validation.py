"""
Unit tests for T017a: Environmental Validation.
"""
import json
import tempfile
from pathlib import Path
import pytest
import yaml

# Mock the config module to avoid dependency on real paths during unit tests
import sys
from unittest.mock import patch, MagicMock

# We need to test the logic in validation.py
# Since validation.py imports from config and utils, we mock those imports.
# However, the task requires us to implement the module. 
# For this test file, we assume the module is importable after installation.
# We will mock the file system interactions.

# Import the module under test
# Note: In a real CI, this would be imported as: from code.analysis import validation
# For this snippet, we assume the path is set up correctly or we import relative to code/
# We will patch the imports inside the module to isolate the test.

@pytest.fixture
def mock_solvent_file(tmp_path):
    """Create a temporary solvents.yaml with version_hash."""
    data = {
        "solvents": [
            {"name": "cyclohexane", "dielectric_constant": 2.02},
            {"name": "toluene", "dielectric_constant": 2.38}
        ],
        "metadata": {
            "version": "1.0.0",
            "version_hash": "abc123def456"
        }
    }
    file_path = tmp_path / "solvents.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(data, f)
    return file_path

@pytest.fixture
def mock_env_log_file(tmp_path):
    """Create a temporary environment_logs.json."""
    data = {
        "runs": [
            {
                "run_id": "run_001",
                "solvent_name": "cyclohexane",
                "dielectric_constant": 2.05, # Slight deviation
                "temperature_c": 25.1,
                "relative_humidity_pct": 50.0
            },
            {
                "run_id": "run_002",
                "solvent_name": "toluene",
                "dielectric_constant": 2.30, # >2% deviation
                "temperature_c": 26.0, # >0.5 deviation
                "relative_humidity_pct": 50.0
            }
        ]
    }
    file_path = tmp_path / "environment_logs.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_load_solvent_reference_missing_hash(mock_solvent_file):
    """Test that ConfigurationError is raised if version_hash is missing."""
    # Modify the mock file to remove hash
    data = {"solvents": [], "metadata": {}}
    with open(mock_solvent_file, 'w') as f:
        yaml.dump(data, f)
    
    with patch('code.analysis.validation.get_chemicals_path') as mock_path:
        mock_path.return_value = mock_solvent_file.parent
        with pytest.raises(Exception) as exc_info:
            from code.analysis import validation
            validation.load_solvent_reference()
        assert "version_hash" in str(exc_info.value)

def test_check_dielectric_deviation():
    """Test dielectric constant deviation logic."""
    ref_data = {
        "solvents": [
            {"name": "test", "dielectric_constant": 100.0}
        ]
    }
    
    # Within tolerance (1%)
    is_valid, msg = validation.check_dielectric_deviation("test", 101.0, ref_data, tolerance_pct=2.0)
    assert is_valid is True
    
    # Outside tolerance (3%)
    is_valid, msg = validation.check_dielectric_deviation("test", 103.0, ref_data, tolerance_pct=2.0)
    assert is_valid is False
    assert "deviation" in msg.lower()

def test_validate_environmental_conditions():
    """Test T/Humidity validation."""
    run_data = {
        "temperature_c": 26.0, # 1.0 deviation from 25.0
        "relative_humidity_pct": 50.0
    }
    
    flags = validation.validate_environmental_conditions(run_data, tolerance_temp=0.5)
    assert len(flags) == 1
    assert "Temperature" in flags[0]

def test_validate_solvent_series_runs(mock_solvent_file, mock_env_log_file):
    """Integration test for the main validation logic."""
    with patch('code.analysis.validation.get_chemicals_path') as mock_chem_path:
        with patch('code.analysis.validation.get_processed_data_path') as mock_proc_path:
            mock_chem_path.return_value = mock_solvent_file.parent
            mock_proc_path.return_value = mock_env_log_file.parent
            
            from code.analysis import validation
            flagged = validation.validate_solvent_series_runs(mock_env_log_file)
            
            assert len(flagged) > 0
            # run_002 should be flagged for both dielectric and temp
            run_002 = next(r for r in flagged if r['run_id'] == 'run_002')
            assert len(run_002['flags']) >= 2