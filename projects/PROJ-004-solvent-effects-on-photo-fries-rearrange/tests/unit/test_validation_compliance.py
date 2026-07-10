import pytest
import json
import tempfile
from pathlib import Path
from analysis.validation import validate_solvent_series_runs, write_validation_report, COMPLIANCE_THRESHOLD_PERCENT

@pytest.fixture
def mock_solvents_lookup():
    return {
        "Hexane": 1.88,
        "Toluene": 2.38,
        "Ethyl Acetate": 6.02,
        "Acetone": 20.7,
        "Ethanol": 24.3
    }

@pytest.fixture
def mock_env_logs():
    return [
        {
            "run_id": "RUN-001",
            "solvent_name": "Hexane",
            "temperature_c": 25.1,
            "relative_humidity_percent": 49.5,
            "measured_dielectric_constant": 1.89
        },
        {
            "run_id": "RUN-002",
            "solvent_name": "Toluene",
            "temperature_c": 24.8,
            "relative_humidity_percent": 50.2,
            "measured_dielectric_constant": 2.38
        },
        {
            "run_id": "RUN-003",
            "solvent_name": "Ethyl Acetate",
            "temperature_c": 25.2,
            "relative_humidity_percent": 51.0,
            "measured_dielectric_constant": 6.02
        },
        {
            "run_id": "RUN-004",
            "solvent_name": "Acetone",
            "temperature_c": 25.0,
            "relative_humidity_percent": 49.8,
            "measured_dielectric_constant": 20.5
        },
        {
            "run_id": "RUN-005",
            "solvent_name": "Ethanol",
            "temperature_c": 24.9,
            "relative_humidity_percent": 50.5,
            "measured_dielectric_constant": 24.3
        }
    ]

def test_compliance_calculation(mock_env_logs, mock_solvents_lookup):
    """Test that compliance percentage is calculated correctly (100% in this case)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = Path(tmpdir) / "env_logs.json"
        with open(logs_path, 'w') as f:
            json.dump(mock_env_logs, f)
        
        results = validate_solvent_series_runs(logs_path, mock_solvents_lookup)
        
        assert results["total_runs"] == 5
        assert results["compliant_runs"] == 5
        assert results["compliance_percent"] == 100.0
        assert results["meets_threshold"] is True

def test_non_compliant_runs(mock_solvents_lookup):
    """Test detection of non-compliant runs (temp out of tolerance)."""
    bad_logs = [
        {
            "run_id": "RUN-001",
            "solvent_name": "Hexane",
            "temperature_c": 26.0,  # Exceeds 25.5
            "relative_humidity_percent": 49.5,
            "measured_dielectric_constant": 1.89
        },
        {
            "run_id": "RUN-002",
            "solvent_name": "Toluene",
            "temperature_c": 25.0,
            "relative_humidity_percent": 50.0,
            "measured_dielectric_constant": 2.38
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = Path(tmpdir) / "env_logs.json"
        with open(logs_path, 'w') as f:
            json.dump(bad_logs, f)
        
        results = validate_solvent_series_runs(logs_path, mock_solvents_lookup)
        
        assert results["total_runs"] == 2
        assert results["compliant_runs"] == 1
        assert results["compliance_percent"] == 50.0
        assert results["meets_threshold"] is False
        assert len(results["failures"]) == 1
        assert "Temp 26.0°C exceeds ±0.5°C tolerance" in results["failures"][0]["reasons"]

def test_write_report(mock_env_logs, mock_solvents_lookup):
    """Test that the compliance report is written correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = Path(tmpdir) / "env_logs.json"
        output_path = Path(tmpdir) / "compliance_report.json"
        
        with open(logs_path, 'w') as f:
            json.dump(mock_env_logs, f)
        
        results = validate_solvent_series_runs(logs_path, mock_solvents_lookup)
        write_validation_report(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert "environmental_compliance_percent" in report
        assert report["environmental_compliance_percent"] == 100.0
        assert report["meets_95_percent_threshold"] is True