"""
Integration test for T032: Quickstart Validation.

This test ensures that the quickstart validation script runs successfully
and all required artifacts are produced.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest
import subprocess

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.config import get_project_root, get_data_root, get_state_root, get_reports_root
from src.utils import write_json, read_json

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_quickstart_validation_script_exists():
    """Verify the validation script exists."""
    script_path = PROJECT_ROOT / "code" / "scripts" / "validate_quickstart.py"
    assert script_path.exists(), "Validation script not found"

def test_quickstart_validation_runs_successfully():
    """Run the validation script and verify it passes."""
    script_path = PROJECT_ROOT / "code" / "scripts" / "validate_quickstart.py"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    
    # Check exit code
    assert result.returncode == 0, f"Validation failed: {result.stderr}"

def test_validation_report_generated():
    """Verify the validation report is generated."""
    report_path = PROJECT_ROOT / "reports" / "quickstart_validation_report.json"
    assert report_path.exists(), "Validation report not generated"
    
    # Verify it's valid JSON
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Verify required sections
    assert "project_structure" in report
    assert "data_availability" in report
    assert "us1" in report
    assert "us2" in report
    assert "us3" in report

def test_all_user_stories_pass():
    """Verify all user stories pass validation."""
    report_path = PROJECT_ROOT / "reports" / "quickstart_validation_report.json"
    assert report_path.exists(), "Validation report not found"
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Check each user story
    assert report["us1"]["success"], "User Story 1 validation failed"
    assert report["us2"]["success"], "User Story 2 validation failed"
    assert report["us3"]["success"], "User Story 3 validation failed"

def test_required_artifacts_exist():
    """Verify all required artifacts exist."""
    required_artifacts = [
        "state/validation_status.json",
        "state/global_error_rate.json",
        "data/baseline_results.csv",
        "data/permutation_results.csv",
        "state/feasibility_gate.json",
        "state/scaling_validation.json",
        "data/timing_profile.csv",
        "data/profiling_logs.json",
        "reports/feasibility_profile.json",
        "data/sensitivity_sweep_raw.csv",
        "data/sensitivity_analysis.csv",
        "data/sensitivity_matrix_full.csv",
    ]
    
    missing = []
    for artifact in required_artifacts:
        path = PROJECT_ROOT / "code" / artifact
        if not path.exists() or path.stat().st_size == 0:
            missing.append(artifact)
    
    assert not missing, f"Missing or empty artifacts: {missing}"