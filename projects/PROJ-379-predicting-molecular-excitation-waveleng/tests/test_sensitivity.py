"""
Integration test for sensitivity sweep and collinearity flags (T022).
Verifies that the sensitivity analysis pipeline produces valid artifacts
and that collinearity flags are correctly structured.
"""
import pytest
import json
import os
from pathlib import Path

# Add project root to path for imports if necessary, though test focuses on file artifacts
project_root = Path(__file__).resolve().parent.parent
data_processed = project_root / "data" / "processed"

collinearity_path = data_processed / "collinearity_flags.json"
sensitivity_report_csv = data_processed / "sensitivity_report.csv"
redundancy_masks_path = data_processed / "redundancy_masks.json"
sensitivity_report_md = data_processed / "sensitivity_report.md"

def test_collinearity_flags_exists_and_valid():
    """Verify collinearity_flags.json exists and has the expected structure."""
    if not collinearity_path.exists():
        pytest.fail("collinearity_flags.json not found. Ensure code/collinearity_check.py (ECFP) has run.")
    
    try:
        with open(collinearity_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"collinearity_flags.json is not valid JSON: {e}")
    
    assert isinstance(data, dict), "collinearity_flags.json must be a dictionary"
    # Expected keys based on T023a implementation: 'flags' (list of bit indices) or 'highly_collinear'
    # The schema allows flexibility but must be a dict.
    assert len(data) > 0, "collinearity_flags.json should contain data"

def test_sensitivity_report_csv_exists_and_valid():
    """Verify sensitivity_report.csv exists and contains data."""
    if not sensitivity_report_csv.exists():
        pytest.fail("sensitivity_report.csv not found. Ensure code/sensitivity.py has run.")
    
    import pandas as pd
    try:
        df = pd.read_csv(sensitivity_report_csv)
    except Exception as e:
        pytest.fail(f"Failed to read sensitivity_report.csv: {e}")
    
    assert len(df) > 0, "sensitivity_report.csv is empty. Expected rows for threshold sweep."
    assert 'threshold' in df.columns, "sensitivity_report.csv must have a 'threshold' column"
    assert 'error_rate' in df.columns, "sensitivity_report.csv must have an 'error_rate' column"

def test_redundancy_masks_exists_and_valid():
    """Verify redundancy_masks.json exists and has the expected structure."""
    if not redundancy_masks_path.exists():
        pytest.fail("redundancy_masks.json not found. Ensure code/collinearity_check.py (GNN) has run.")
    
    try:
        with open(redundancy_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"redundancy_masks.json is not valid JSON: {e}")
    
    assert isinstance(data, dict), "redundancy_masks.json must be a dictionary"
    # Structure: { "subgraph_id": boolean }
    for key, value in data.items():
        assert isinstance(key, str), "Keys must be subgraph IDs (strings)"
        assert isinstance(value, bool), "Values must be booleans indicating redundancy"

def test_sensitivity_report_md_exists():
    """Verify the narrative sensitivity report exists."""
    if not sensitivity_report_md.exists():
        pytest.fail("sensitivity_report.md not found. Ensure code/sensitivity.py generated the narrative.")
    
    with open(sensitivity_report_md, 'r') as f:
        content = f.read()
    
    assert len(content) > 100, "sensitivity_report.md appears too short to be a valid report."
    assert "Threshold" in content or "threshold" in content, "Report should discuss thresholds."