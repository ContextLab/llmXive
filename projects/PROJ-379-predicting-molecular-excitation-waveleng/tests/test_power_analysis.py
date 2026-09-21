"""
Test for power analysis logic (T018 related).
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
power_analysis_path = project_root / "data" / "processed" / "power_analysis.json"

def test_power_analysis_structure():
    """Verify power_analysis.json structure."""
    if not power_analysis_path.exists():
        pytest.skip("power_analysis.json not found.")
    
    with open(power_analysis_path, 'r') as f:
        data = json.load(f)
    
    assert "n" in data, "Missing 'n' in power_analysis.json"
    assert "power_status" in data, "Missing 'power_status' in power_analysis.json"
    
    n = data["n"]
    status = data["power_status"]
    
    if n >= 50:
        assert status == "high_power", f"Expected high_power for n={n}, got {status}"
    else:
        assert status == "low_power", f"Expected low_power for n={n}, got {status}"
