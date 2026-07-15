"""
Integration test for T029: Quickstart Validation.

This test verifies that the quickstart validation script runs successfully
and produces the expected outputs. It is designed to be run in the CI environment.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"

@pytest.mark.integration
def test_quickstart_validation_script():
    """Test that the quickstart validation script runs without errors."""
    script_path = CODE_DIR / "quickstart_validation.py"
    
    assert script_path.exists(), f"Script not found: {script_path}"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=600  # Allow more time for full pipeline
    )
    
    # Check exit code
    assert result.returncode == 0, (
        f"Quickstart validation failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

@pytest.mark.integration
def test_validation_summary_generated():
    """Test that the validation summary JSON is generated."""
    summary_path = ANALYSIS_DIR / "quickstart_validation_summary.json"
    
    # The summary might not exist if the test is run before the main script
    # In a real CI flow, this test would run after the main script
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
        
        assert summary["status"] == "passed"
        assert summary["task_id"] == "T029"
        assert summary["environment"] == "cpu-only"
    else:
        # If the file doesn't exist, it means the main script hasn't run yet
        # This is acceptable in a test suite that runs independently
        pytest.skip("Validation summary not generated (main script may not have run).")

@pytest.mark.integration
def test_expected_outputs_exist():
    """Test that the pipeline produces the expected output files."""
    expected_files = [
        "data/processed/lzc_metrics.csv",
        "data/processed/pe_metrics.csv",
        "data/analysis/correlation_results.json",
        "data/analysis/sensitivity_table.csv",
        "data/analysis/final_report.txt"
    ]
    
    missing = []
    for file_path in expected_files:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing.append(file_path)
        elif full_path.stat().st_size == 0:
            missing.append(f"{file_path} (empty)")
    
    if missing:
        pytest.fail(f"Missing or empty expected files: {missing}")
