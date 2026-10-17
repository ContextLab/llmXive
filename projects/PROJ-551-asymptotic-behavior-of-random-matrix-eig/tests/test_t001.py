import json
import pytest
from pathlib import Path
from datetime import datetime

def test_single_run_json_schema():
    """Verify that the output JSON conforms to the SimulationRun and EigenvalueResult contracts."""
    result_path = Path("data/processed/single_run_results.json")
    assert result_path.exists(), "Result file should exist"
    
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    # SimulationRun fields
    required_run_fields = {
        "run_id", "timestamp", "seed", "N", "k", "theta", 
        "pattern_type", "computation_time_ms", "empirical_bulk_edge", "eigenvalues"
    }
    assert required_run_fields.issubset(data.keys())
    
    # Timestamp format
    try:
        datetime.fromisoformat(data["timestamp"])
    except ValueError:
        pytest.fail("Timestamp is not ISO-8601 formatted")
    
    # EigenvalueResult fields
    run_id = data["run_id"]
    for eig in data["eigenvalues"]:
        required_eig_fields = {
            "run_id", "eigenvalue_index", "value", "is_outlier", "theoretical_bbp", "deviation"
        }
        assert required_eig_fields.issubset(eig.keys())
        assert eig["run_id"] == run_id, "Eigenvalue run_id must match parent run_id"

def test_outlier_logic():
    """Verify that the outlier rule (value > edge + 0.05) is correctly applied."""
    result_path = Path("data/processed/single_run_results.json")
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    edge = data["empirical_bulk_edge"]
    for eig in data["eigenvalues"]:
        expected_outlier = eig["value"] > (edge + 0.05)
        assert eig["is_outlier"] == expected_outlier, f"Outlier flag mismatch for value {eig['value']} with edge {edge}"

def test_reproducibility():
    """Verify that running the same params produces the same top eigenvalue."""
    import subprocess
    cmd = ["python", "code/main.py", "--mode", "single", "--N", "1000", "--seed", "42", "--theta", "2.5", "--k", "1", "--pattern", "diagonal"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(res.stdout)
    top_val = data["eigenvalues"][0]["value"]
    
    # Compare against the recorded file
    with open("data/processed/single_run_results.json", 'r') as f:
        recorded = json.load(f)
    recorded_val = recorded["eigenvalues"][0]["value"]
    
    assert abs(top_val - recorded_val) < 1e-6
