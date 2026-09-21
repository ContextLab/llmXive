"""
Integration test for sensitivity sweep and collinearity flags (T022).
"""
import pytest
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
collinearity_path = project_root / "data" / "processed" / "collinearity_flags.json"
sensitivity_report_csv = project_root / "data" / "processed" / "sensitivity_report.csv"
redundancy_masks_path = project_root / "data" / "processed" / "redundancy_masks.json"

def test_collinearity_flags_exists():
    """Verify collinearity_flags.json exists and has structure."""
    if not collinearity_path.exists():
        pytest.skip("collinearity_flags.json not found.")
    
    with open(collinearity_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, dict), "collinearity_flags.json must be a dict"

def test_sensitivity_report_exists():
    """Verify sensitivity_report.csv exists."""
    if not sensitivity_report_csv.exists():
        pytest.skip("sensitivity_report.csv not found.")
    
    import pandas as pd
    df = pd.read_csv(sensitivity_report_csv)
    assert len(df) > 0, "sensitivity_report.csv is empty"

def test_redundancy_masks_exists():
    """Verify redundancy_masks.json exists."""
    if not redundancy_masks_path.exists():
        pytest.skip("redundancy_masks.json not found.")
    
    with open(redundancy_masks_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, dict), "redundancy_masks.json must be a dict"
