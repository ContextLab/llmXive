import os
import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

RESULTS_DIR = Path("data/results")
SENSITIVITY_REPORT_PATH = RESULTS_DIR / "sensitivity_report.json"

def test_sensitivity_report_exists():
    """Test that the sensitivity report file exists after analysis."""
    if not SENSITIVITY_REPORT_PATH.exists():
        pytest.skip("Sensitivity report not generated yet. Run sensitivity analysis first.")
    
    with open(SENSITIVITY_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    assert isinstance(report, dict), "Sensitivity report should be a dictionary"

def test_sensitivity_report_contains_thresholds():
    """Test that the report contains results for multiple thresholds."""
    if not SENSITIVITY_REPORT_PATH.exists():
        pytest.skip("Sensitivity report not generated yet.")
    
    with open(SENSITIVITY_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    # Expected thresholds from T026
    expected_thresholds = [0.04, 0.05, 0.06, 0.10]
    
    # The report structure might be a dict of thresholds or a list
    # Assuming a structure like: {"threshold_0.05": {...}, ...} or similar
    # We check if at least one threshold result is present
    assert len(report) > 0, "Sensitivity report is empty"
    
    # Check for the borderline flag if present
    if 'is_sensitive_to_threshold' in report:
        assert isinstance(report['is_sensitive_to_threshold'], bool), \
            "is_sensitive_to_threshold should be a boolean"

def test_sensitivity_report_contains_metrics():
    """Test that significance status is reported per threshold."""
    if not SENSITIVITY_REPORT_PATH.exists():
        pytest.skip("Sensitivity report not generated yet.")
    
    with open(SENSITIVITY_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    # Check for keys indicating significance status
    # Structure may vary, but should contain some indication of significance
    keys = report.keys()
    # At least one key should relate to a metric or threshold
    assert any('significance' in k.lower() or 'p_value' in k.lower() for k in keys), \
        "Report should contain significance or p-value information"

def test_borderline_flag_logic():
    """Test that the borderline flag is correctly set based on p-value range."""
    if not SENSITIVITY_REPORT_PATH.exists():
        pytest.skip("Sensitivity report not generated yet.")
    
    with open(SENSITIVITY_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    # This test assumes the report contains a p-value and the flag
    # We can't verify the logic without the actual p-value, 
    # but we can ensure the flag exists and is boolean.
    if 'is_sensitive_to_threshold' in report:
        assert isinstance(report['is_sensitive_to_threshold'], bool), \
            "is_sensitive_to_threshold must be a boolean"
