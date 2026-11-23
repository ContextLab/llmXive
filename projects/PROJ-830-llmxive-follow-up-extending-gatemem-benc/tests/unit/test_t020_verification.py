"""
Unit test to verify the existence and validity of T020 output artifacts.
"""
import os
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "t020_medical_access_control_report.json"

def test_t020_report_exists():
    """Verify that the T020 report file was generated."""
    assert REPORT_PATH.exists(), f"T020 report file not found at {REPORT_PATH}"

def test_t020_report_content():
    """Verify the T020 report contains valid data."""
    if not REPORT_PATH.exists():
        pytest.skip("Report file not generated yet. Run test_t020_medical_domain first.")
    
    with open(REPORT_PATH, "r") as f:
        data = json.load(f)
    
    assert data["task_id"] == "T020", "Task ID mismatch."
    assert data["domain"] == "medical", "Domain mismatch."
    assert "gatekeeper_ac_score" in data, "Missing Access Control score."
    
    score = data["gatekeeper_ac_score"]
    assert isinstance(score, float), "Score must be a float."
    assert 0.0 <= score <= 1.0, f"Score {score} out of valid range [0, 1]."
    
    assert data["status"] == "completed", "Task status is not completed."

def test_t020_results_files_exist():
    """Verify that the intermediate result files exist."""
    gatekeeper_path = PROJECT_ROOT / "data" / "processed" / "gatekeeper_results_medical.json"
    baseline_path = PROJECT_ROOT / "data" / "processed" / "baseline_longcontext_results_medical.json"
    
    assert gatekeeper_path.exists(), "Gatekeeper results file missing."
    assert baseline_path.exists(), "Baseline results file missing."
    
    # Verify they are not empty
    with open(gatekeeper_path) as f:
        g_data = json.load(f)
        assert len(g_data) > 0, "Gatekeeper results are empty."
    
    with open(baseline_path) as f:
        b_data = json.load(f)
        assert len(b_data) > 0, "Baseline results are empty."