import json
import numpy as np
from pathlib import Path
import pytest
import subprocess

def test_single_run_reproducibility():
    """
    Verify that running the same command produces the same top eigenvalue
    within 1e-6 tolerance.
    """
    cmd = [
        "python", "code/main.py", 
        "--mode", "single", 
        "--N", "1000", 
        "--seed", "42", 
        "--theta", "2.5", 
        "--k", "1", 
        "--pattern", "diagonal",
        "--output", "data/processed/repro_check_1.json"
    ]
    
    # First run
    subprocess.run(cmd, check=True)
    with open("data/processed/repro_check_1.json", "r") as f:
        res1 = json.load(f)
    val1 = res1["eigenvalues"][0]["value"]
    
    # Second run (different output file)
    cmd[11] = "data/processed/repro_check_2.json"
    subprocess.run(cmd, check=True)
    with open("data/processed/repro_check_2.json", "r") as f:
        res2 = json.load(f)
    val2 = res2["eigenvalues"][0]["value"]
    
    assert abs(val1 - val2) < 1e-6

def test_json_structure():
    """Verify the JSON output conforms to the expected contract."""
    path = Path("data/processed/single_run_results.json")
    assert path.exists()
    
    with open(path, "r") as f:
        data = json.load(f)
    
    # SimulationRun keys
    expected_keys = {"run_id", "timestamp", "seed", "N", "k", "theta", 
                     "pattern_type", "support_density", "computation_time_ms", 
                     "empirical_bulk_edge", "eigenvalues"}
    assert expected_keys.issubset(data.keys())
    
    # EigenvalueResult keys
    eig_keys = {"run_id", "eigenvalue_index", "value", "is_outlier", "theoretical_bbp", "deviation"}
    assert eig_keys.issubset(data["eigenvalues"][0].keys())
    assert data["eigenvalues"][0]["run_id"] == data["run_id"]