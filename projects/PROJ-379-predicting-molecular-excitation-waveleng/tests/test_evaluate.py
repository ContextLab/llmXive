"""
Test task for SC-001 logic (T017).
Verifies sc001_status logic in evaluate.py.
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
metrics_path = project_root / "data" / "processed" / "metrics_partial.json"

def test_sc001_status_logic():
    """
    Verify sc001_status is set correctly based on MAE and power status.
    Logic:
    - If n >= 50 and MAE < 30 -> PASS
    - If n < 50 -> LOW_POWER
    - If MAE > 50 -> Failure (implied logic, though task says Failure is MAE > 50)
    """
    if not metrics_path.exists():
        pytest.skip("metrics_partial.json not found.")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    mae = data.get("mae")
    power_status = data.get("power_status") # "high_power" or "low_power"
    sc001_status = data.get("sc001_status")
    
    assert sc001_status is not None, "sc001_status must be present"
    
    if power_status == "low_power":
        assert sc001_status == "LOW_POWER", f"Expected LOW_POWER when n < 50, got {sc001_status}"
    elif power_status == "high_power":
        if mae < 30:
            assert sc001_status == "PASS", f"Expected PASS when MAE < 30 and high power, got {sc001_status}"
        elif mae > 50:
            # Task says Failure is MAE > 50. Status might be "FAIL" or similar.
            assert sc001_status != "PASS", f"Expected failure status when MAE > 50, got {sc001_status}"
