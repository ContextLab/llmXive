"""
Test for final metrics.json structure (T027, T044 related).
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
metrics_path = project_root / "data" / "processed" / "metrics.json"

def test_metrics_json_complete():
    """Verify metrics.json contains all required keys and valid data types."""
    if not metrics_path.exists():
        pytest.skip("metrics.json not found.")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    required_keys = [
        "mae", "r2", "wilcoxon_p_value", "sc001_status", 
        "collinearity_flags", "redundancy_masks", "power_status", 
        "attribution_results", "narrative_summary"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in metrics.json"
    
    # Check types (allowing None/null)
    assert data["mae"] is None or isinstance(data["mae"], (int, float))
    assert data["r2"] is None or isinstance(data["r2"], (int, float))
    assert data["sc001_status"] is None or isinstance(data["sc001_status"], str)
    assert data["power_status"] is None or isinstance(data["power_status"], str)
    assert data["narrative_summary"] is None or isinstance(data["narrative_summary"], str)