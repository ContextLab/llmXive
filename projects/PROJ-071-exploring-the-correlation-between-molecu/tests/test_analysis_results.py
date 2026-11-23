import json
import os
from pathlib import Path
import pytest
from datetime import datetime

# Add code to path if needed, assuming standard project structure
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_analysis_results_schema():
    """
    T026 Verification: Check that data/processed/analysis_results.json exists and matches schema.
    """
    # Determine path relative to project root
    # Assuming tests are in tests/ and data is in data/
    project_root = Path(__file__).parent.parent
    result_path = project_root / "data" / "processed" / "analysis_results.json"

    assert result_path.exists(), f"Analysis results file not found at {result_path}"

    with open(result_path, 'r') as f:
        data = json.load(f)

    # Check required keys
    required_keys = ["status", "N", "R2", "p_values", "coefficients", "methodology", "timestamp"]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"

    # Check types
    assert isinstance(data["status"], str)
    assert data["status"] in ["PASS", "FAIL"], f"Invalid status: {data['status']}"

    assert isinstance(data["N"], int), f"N must be int, got {type(data['N'])}"
    
    if data["status"] == "PASS":
        assert data["R2"] is not None, "R2 must be present for PASS status"
        assert isinstance(data["R2"], float), "R2 must be float"
        assert data["p_values"] is not None, "p_values must be present for PASS status"
        assert isinstance(data["p_values"], dict), "p_values must be dict"
        assert data["coefficients"] is not None, "coefficients must be present for PASS status"
        assert isinstance(data["coefficients"], dict), "coefficients must be dict"
    else:
        # If FAIL, R2, p_values, coefficients should be null or absent (schema says null)
        # We allow them to be None or missing if status is FAIL, but strict schema says null
        if data["R2"] is not None:
            assert isinstance(data["R2"], float) or data["R2"] is None
        if data["p_values"] is not None:
            assert isinstance(data["p_values"], dict) or data["p_values"] is None
        if data["coefficients"] is not None:
            assert isinstance(data["coefficients"], dict) or data["coefficients"] is None

    assert data["methodology"] == "MLR+LASSO"

    # Check timestamp format
    try:
        datetime.fromisoformat(data["timestamp"])
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {data['timestamp']}")

def test_analysis_results_logic():
    """
    T026 Verification: If gate failed, status must be FAIL.
    """
    project_root = Path(__file__).parent.parent
    result_path = project_root / "data" / "processed" / "analysis_results.json"
    gate_path = project_root / "data" / "gate_status.json"

    if not result_path.exists():
        pytest.skip("Analysis results not generated yet")

    with open(result_path, 'r') as f:
        result_data = json.load(f)

    if gate_path.exists():
        with open(gate_path, 'r') as f:
            gate_data = json.load(f)
        
        if gate_data.get("status") == "FAIL":
            assert result_data["status"] == "FAIL", "If gate failed, analysis result status must be FAIL"
            assert result_data["N"] == gate_data.get("N", 0), "N in result should match gate N"