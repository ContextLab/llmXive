import json
import os
from pathlib import Path
import pytest

# Ensure we can import from code
sys_path = Path(__file__).parent.parent / "code"
if str(sys_path) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path))

from analysis import save_analysis_results_wrapper, get_data_path

def test_save_analysis_results_schema():
    """Test T026: Verify the schema of analysis_results.json."""
    data_root = get_data_path()
    output_path = data_root / "processed" / "analysis_results.json"
    
    # Ensure directory exists for test
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Test PASS case
    save_analysis_results_wrapper(
        status="PASS",
        n=50,
        r2=0.75,
        p_values={"TPSA": 0.01, "MW": 0.05},
        coefficients={"TPSA": -0.5, "MW": 0.1},
        diagnostics={
            "shapiro_wilk": {"stat": 0.98, "p": 0.5},
            "breusch_pagan": {"stat": 1.2, "p": 0.2}
        }
    )

    assert output_path.exists(), "analysis_results.json not created"
    
    with open(output_path, "r") as f:
        data = json.load(f)

    assert data["status"] == "PASS"
    assert data["N"] == 50
    assert data["R2"] == 0.75
    assert "p_values" in data
    assert "coefficients" in data
    assert data["methodology"] == "MLR+LASSO"
    assert "timestamp" in data
    assert "diagnostics" in data
    assert "shapiro_wilk" in data["diagnostics"]
    assert "breusch_pagan" in data["diagnostics"]

    # Test FAIL case
    save_analysis_results_wrapper(
        status="FAIL",
        n=10,
        r2=None,
        p_values=None,
        coefficients=None,
        diagnostics=None
    )

    with open(output_path, "r") as f:
        data_fail = json.load(f)

    assert data_fail["status"] == "FAIL"
    assert data_fail["N"] == 10
    assert data_fail["R2"] is None
    assert data_fail["p_values"] is None
    assert data_fail["coefficients"] is None

    # Cleanup
    output_path.unlink()