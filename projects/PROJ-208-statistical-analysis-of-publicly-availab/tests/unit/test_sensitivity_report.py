"""
Unit tests for T025c: Sensitivity Report Generator.
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from analysis.sensitivity_report_generator import (
    load_sensitivity_sweep,
    generate_stability_report,
    save_report
)

@pytest.fixture
def sample_sweep_data():
    """Sample data mimicking T025b-3 output."""
    return {
        "thresholds": {
            "0.01": {"proportion": 0.123, "details": "test"},
            "0.05": {"proportion": 0.456, "details": "test"},
            "0.10": {"proportion": 0.789, "details": "test"},
            "0.20": {"proportion": 0.99, "details": "test"}
        }
    }

@pytest.fixture
def temp_input_file(sample_sweep_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_sweep_data, f)
        yield Path(f.name)
    Path(f.name).unlink()

def test_load_sensitivity_sweep_success(temp_input_file, sample_sweep_data):
    result = load_sensitivity_sweep(temp_input_file)
    assert result == sample_sweep_data

def test_load_sensitivity_sweep_missing_file():
    with pytest.raises(FileNotFoundError):
        load_sensitivity_sweep(Path("/nonexistent/path.json"))

def test_generate_stability_report_correct_keys(sample_sweep_data):
    report = generate_stability_report(sample_sweep_data)
    assert 0.01 in report
    assert 0.05 in report
    assert 0.1 in report
    assert report[0.01] == 0.123
    assert report[0.05] == 0.456
    assert report[0.1] == 0.789

def test_generate_stability_report_missing_threshold(sample_sweep_data):
    # Remove 0.01 key
    incomplete_data = {
        "thresholds": {
            "0.05": {"proportion": 0.456},
            "0.10": {"proportion": 0.789}
        }
    }
    with pytest.raises(ValueError, match="Threshold 0.01 missing"):
        generate_stability_report(incomplete_data)

def test_generate_stability_report_missing_proportion_key(sample_sweep_data):
    # Modify 0.01 to lack 'proportion'
    bad_data = {
        "thresholds": {
            "0.01": {"wrong_key": 0.123},
            "0.05": {"proportion": 0.456},
            "0.10": {"proportion": 0.789}
        }
    }
    with pytest.raises(ValueError, match="Could not find 'proportion'"):
        generate_stability_report(bad_data)

def test_save_report(tmp_path):
    report = {0.01: 0.1, 0.05: 0.5, 0.1: 0.9}
    output_file = tmp_path / "test_report.json"
    
    save_report(report, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    # JSON keys are strings
    assert loaded["0.01"] == 0.1
    assert loaded["0.05"] == 0.5
    assert loaded["0.1"] == 0.9