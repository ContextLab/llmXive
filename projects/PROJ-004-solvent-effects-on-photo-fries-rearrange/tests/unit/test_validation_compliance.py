"""
Unit tests for T017b: Environmental Compliance Calculation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Mock config paths for testing
@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        chemicals_dir = tmp_path / "data" / "chemicals"
        chemicals_dir.mkdir(parents=True)
        
        # Create a mock solvents.yaml
        solvents_data = {
            "solvents": [
                {"name": "hexane", "dielectric_constant": 1.88, "source_id": "NIST", "version_hash": "test"},
                {"name": "toluene", "dielectric_constant": 2.38, "source_id": "NIST", "version_hash": "test"},
            ]
        }
        with open(chemicals_dir / "solvents.yaml", 'w') as f:
            import yaml
            yaml.dump(solvents_data, f)

        # Create mock environment logs
        logs = [
            {"run_id": "RUN-001", "solvent": "hexane", "logged_dielectric": 1.90, "logged_temperature": 25.0, "logged_humidity": 45.0, "timestamp": "2026-05-16T10:00:00Z"},
            {"run_id": "RUN-002", "solvent": "toluene", "logged_dielectric": 2.45, "logged_temperature": 25.0, "logged_humidity": 45.0, "timestamp": "2026-05-16T10:15:00Z"}, # Valid
            {"run_id": "RUN-003", "solvent": "hexane", "logged_dielectric": 5.00, "logged_temperature": 25.0, "logged_humidity": 45.0, "timestamp": "2026-05-16T10:30:00Z"}, # Invalid dielectric
        ]
        with open(processed_dir / "environment_logs.json", 'w') as f:
            json.dump(logs, f)

        yield tmp_path

@pytest.fixture
def patched_config(temp_dirs):
    with patch('config.get_processed_data_path', return_value=temp_dirs / "data" / "processed"):
        with patch('config.get_chemicals_path', return_value=temp_dirs / "data" / "chemicals"):
            yield

def test_calculate_environmental_compliance(patched_config):
    from analysis.validation import calculate_environmental_compliance, write_compliance_report

    # Run calculation
    result = calculate_environmental_compliance()

    assert 'total_runs' in result
    assert 'compliant_runs' in result
    assert 'environmental_compliance_percent' in result
    
    # We have 3 runs. 
    # RUN-001: hexane, 1.90 vs 1.88 -> 1.06% dev (Valid), Temp 25 (Valid), Hum 45 (Valid) -> Compliant
    # RUN-002: toluene, 2.45 vs 2.38 -> 2.94% dev (Invalid > 2%), Temp 25 (Valid), Hum 45 (Valid) -> Non-Compliant
    # RUN-003: hexane, 5.00 vs 1.88 -> Huge dev (Invalid), Temp 25 (Valid), Hum 45 (Valid) -> Non-Compliant
    # Expected: 1 compliant out of 3.
    
    assert result['total_runs'] == 3
    assert result['compliant_runs'] == 1
    assert abs(result['environmental_compliance_percent'] - 33.33) < 0.1

def test_write_compliance_report(patched_config):
    from analysis.validation import calculate_environmental_compliance, write_compliance_report
    import json

    result = calculate_environmental_compliance()
    output_path = write_compliance_report(result)

    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded['environmental_compliance_percent'] == result['environmental_compliance_percent']
    assert 'details' in loaded
    assert len(loaded['details']) == 3