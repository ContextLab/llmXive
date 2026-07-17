import json
import pytest
from pathlib import Path
from code.src.validation.validate_batch import (
    check_sc001_graph_count,
    check_sc002_runtime,
    check_sc005_sensitivity_sweep,
    generate_validation_report
)

@pytest.fixture
def temp_data_dir(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    return tmp_path

def test_sc001_pass(temp_data_dir):
    manifest = {
        "total_generated": 10,
        "valid_count": 10,
        "success_rate": 1.0,
        "total_attempts": 10,
        "failed_graphs": []
    }
    manifest_path = temp_data_dir / "raw" / "global_batch_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    result = check_sc001_graph_count(manifest_path)
    assert result["status"] == "PASS"
    assert result["details"]["actual_count"] == 10

def test_sc001_fail(temp_data_dir):
    manifest = {
        "total_generated": 2,
        "valid_count": 2,
        "success_rate": 1.0,
        "total_attempts": 2,
        "failed_graphs": []
    }
    manifest_path = temp_data_dir / "raw" / "global_batch_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    result = check_sc001_graph_count(manifest_path)
    assert result["status"] == "FAIL"
    assert result["details"]["actual_count"] == 2

def test_sc005_pass(temp_data_dir):
    sweep_data = {
        "cutoffs": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    }
    sweep_path = temp_data_dir / "analysis" / "sensitivity_sweep.json"
    with open(sweep_path, 'w') as f:
        json.dump(sweep_data, f)

    result = check_sc005_sensitivity_sweep(sweep_path)
    assert result["status"] == "PASS"
    assert result["details"]["actual_cutoffs"] == 6

def test_sc005_fail(temp_data_dir):
    sweep_data = {
        "cutoffs": [0.1, 0.2, 0.3]
    }
    sweep_path = temp_data_dir / "analysis" / "sensitivity_sweep.json"
    with open(sweep_path, 'w') as f:
        json.dump(sweep_data, f)

    result = check_sc005_sensitivity_sweep(sweep_path)
    assert result["status"] == "FAIL"
    assert result["details"]["actual_cutoffs"] == 3

def test_generate_report(temp_data_dir, tmp_path):
    # Setup manifest
    manifest = {"total_generated": 10, "valid_count": 10, "success_rate": 1.0, "total_attempts": 10, "failed_graphs": []}
    manifest_path = temp_data_dir / "raw" / "global_batch_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    # Setup run log
    run_log = {"total_runtime_seconds": 100}
    run_log_path = temp_data_dir / "run_log.json"
    with open(run_log_path, 'w') as f:
        json.dump(run_log, f)

    # Setup sensitivity sweep
    sweep_data = {"cutoffs": [0.1, 0.2, 0.3, 0.4, 0.5]}
    sweep_path = temp_data_dir / "analysis" / "sensitivity_sweep.json"
    with open(sweep_path, 'w') as f:
        json.dump(sweep_data, f)

    # Create a dummy config
    config_path = tmp_path / "config.yaml"
    config_path.write_text("paths:\n  data: " + str(temp_data_dir))

    output_path = tmp_path / "validation_report.json"

    report = generate_validation_report(config_path, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["sc_001_status"] == "PASS"
    assert saved_report["sc_005_status"] == "PASS"
    # SC-002 depends on runtime logic, assuming it passes if data is present
    assert "sc_002_status" in saved_report