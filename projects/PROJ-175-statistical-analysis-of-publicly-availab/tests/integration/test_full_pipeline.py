import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

DATA_DIR = project_root / "data"

@pytest.mark.integration
def test_pipeline_execution_log_exists():
    """Verify that T043 produces the required final_execution_log.json."""
    log_path = DATA_DIR / "final_execution_log.json"
    assert log_path.exists(), f"Final execution log not found at {log_path}"

    with open(log_path, "r") as f:
        data = json.load(f)

    assert "overall_success" in data, "Missing 'overall_success' field"
    assert "total_runtime_seconds" in data, "Missing 'total_runtime_seconds' field"
    assert "peak_memory_gb" in data, "Missing 'peak_memory_gb' field"
    assert "steps" in data, "Missing 'steps' field"
    
    # Verify structure of steps
    assert isinstance(data["steps"], list), "'steps' must be a list"
    if len(data["steps"]) > 0:
        step = data["steps"][0]
        assert "step" in step, "Step missing 'step' name"
        assert "success" in step, "Step missing 'success' status"

@pytest.mark.integration
def test_ci_validation_report_exists():
    """Verify that CI validation report is generated."""
    report_path = DATA_DIR / "ci_validation_report.json"
    assert report_path.exists(), f"CI validation report not found at {report_path}"

    with open(report_path, "r") as f:
        data = json.load(f)

    assert "passed" in data, "Missing 'passed' field in CI report"
    assert "total_time_seconds" in data, "Missing 'total_time_seconds' in CI report"

@pytest.mark.integration
def test_prerequisite_artifacts_exist():
    """Verify that key artifacts from previous tasks exist."""
    required_files = [
        "verification_report.json",
        "power_analysis_logistic.json",
        "power_analysis_bayesian.json",
        "model_comparison.json",
        "auc_delta_metrics.json"
    ]

    for filename in required_files:
        path = DATA_DIR / filename
        assert path.exists(), f"Prerequisite artifact missing: {filename}"

    # Check verification report success
    with open(DATA_DIR / "verification_report.json", "r") as f:
        verify_data = json.load(f)
    assert verify_data.get("status") == "SUCCESS", "Verification report indicates failure"