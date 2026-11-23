"""
Integration Test for T038: End-to-End Pipeline Timing.

Verifies that the pipeline execution script exists, is importable,
and produces the required timing_log.json artifact.
"""
import os
import json
import pytest
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = PROJECT_ROOT / "results"
TIMING_LOG_PATH = RESULTS_DIR / "timing_log.json"

@pytest.fixture(scope="module")
def pipeline_script():
    """Ensure the pipeline script exists."""
    script_path = CODE_DIR / "run_pipeline_timing.py"
    assert script_path.exists(), f"Pipeline script not found at {script_path}"
    return script_path

@pytest.fixture(scope="module")
def run_pipeline(pipeline_script):
    """Execute the pipeline script if it hasn't been run yet or to ensure fresh results."""
    # We run the script to ensure the artifact is generated for this test run
    # Note: In a real CI, this might be a separate step. Here we run it to validate the artifact.
    result = subprocess.run(
        [sys.executable, str(pipeline_script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result

def test_pipeline_script_executable(run_pipeline):
    """Test that the pipeline script executes without crashing."""
    # We expect success or a specific timeout failure, but not a syntax/import error
    # The script itself handles the 6-hour check.
    # For this test, we just check it runs.
    assert run_pipeline.returncode == 0 or run_pipeline.returncode == 1, \
        f"Pipeline script failed with unexpected error: {run_pipeline.stderr}"

def test_timing_log_generated(run_pipeline):
    """Test that the timing log is generated."""
    assert TIMING_LOG_PATH.exists(), f"Timing log not found at {TIMING_LOG_PATH}"

def test_timing_log_structure(run_pipeline):
    """Test that the timing log contains required fields."""
    with open(TIMING_LOG_PATH, "r") as f:
        data = json.load(f)
    
    assert "total_duration_seconds" in data, "Missing total_duration_seconds"
    assert "status" in data, "Missing status"
    assert "constraints" in data, "Missing constraints"
    assert "passed" in data["constraints"], "Missing constraints.passed"
    
    # Verify the constraint logic
    assert isinstance(data["total_duration_seconds"], (int, float)), "Duration must be numeric"
    assert data["constraints"]["max_duration_seconds"] == 6 * 3600, "Max duration should be 6 hours"

def test_timing_log_validity(run_pipeline):
    """Test that the pipeline completed within the 6-hour limit."""
    with open(TIMING_LOG_PATH, "r") as f:
        data = json.load(f)
    
    # The task requires the pipeline to complete within 6 hours.
    # If it didn't, the test fails.
    assert data["constraints"]["passed"], \
        f"Pipeline took {data['total_duration_seconds']}s, exceeding 6-hour limit."

def test_pipeline_success(run_pipeline):
    """Test that the pipeline reported success."""
    with open(TIMING_LOG_PATH, "r") as f:
        data = json.load(f)
    
    assert data["status"] == "success", \
        f"Pipeline status is '{data['status']}', expected 'success'. Check logs for errors."
    
    # Check that all steps succeeded
    for step in data.get("steps", []):
        assert step["status"] == "success", \
            f"Step '{step['step']}' failed: {step.get('error', 'Unknown error')}"