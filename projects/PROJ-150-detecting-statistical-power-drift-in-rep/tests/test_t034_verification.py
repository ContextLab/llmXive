"""
Tests for Task T034: Pipeline Verification on Static Subset.
"""
import os
import json
import pytest
from pathlib import Path

# Assuming the project root is the parent of the tests directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

def test_verification_report_exists():
    """Test that the T034 verification report was generated."""
    report_path = RESULTS_DIR / "t034_verification_report.json"
    assert report_path.exists(), f"Verification report not found at {report_path}"

def test_verification_report_structure():
    """Test that the verification report has the expected structure."""
    report_path = RESULTS_DIR / "t034_verification_report.json"
    if not report_path.exists():
        pytest.skip("Report not generated yet.")
        
    with open(report_path, "r") as f:
        report = json.load(f)
    
    assert "task_id" in report
    assert report["task_id"] == "T034"
    assert "status" in report
    assert "timestamp" in report
    assert report["status"] == "success"

def test_pipeline_outputs_exist():
    """Test that all expected pipeline outputs exist."""
    expected_outputs = [
        "data/derived/cleaned_data.csv",
        "data/derived/grouping_validation.json",
        "data/derived/pilot_ols_model.pkl",
        "data/derived/residuals.csv",
        "results/lmm_final_summary.json",
        "results/power_drift_scatter.png",
        "results/permutation_pvalue.json",
        "results/sensitivity_report.json",
        "results/aggregated_drift.json"
    ]
    
    missing = []
    for rel_path in expected_outputs:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
    
    assert len(missing) == 0, f"Missing expected outputs: {missing}"
