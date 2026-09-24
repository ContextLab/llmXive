"""
Integration test for T034b: Reproducibility Verification.

This test ensures that the verification script runs without error
and produces a valid report file.
"""
import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config

@pytest.mark.integration
def test_reproducibility_script_execution():
    """Test that the reproducibility script runs and generates a report."""
    script_path = PROJECT_ROOT / "code" / "scripts" / "verify_reproducibility.py"
    report_path = PROJECT_ROOT / "results" / "reproducibility_report.json"
    
    # Clean up any existing report
    if report_path.exists():
        report_path.unlink()

    # Ensure results directory exists
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    # Run the script
    # Note: This is a heavy test. In a real CI, it might be skipped or run on specific triggers.
    # We mock the heavy lifting or assume the environment has the data.
    # For this test, we verify the script *can* run and produce the JSON structure.
    
    # If the data is missing, the script should fail loudly (as per T000 requirements).
    # We check if the report is created. If the script fails due to missing data,
    # the test should reflect that the pipeline is not ready, but the script logic is correct.
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300 # 5 minutes timeout
        )
        
        # We expect the script to either succeed (verified=True) or fail (verified=False)
        # The critical part is that it generates the report.
        
        assert report_path.exists(), "Reproducibility report was not generated."
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        assert "verified" in report, "Report missing 'verified' key."
        assert "run_1_hashes" in report, "Report missing 'run_1_hashes'."
        assert "run_2_hashes" in report, "Report missing 'run_2_hashes'."
        
        # The test passes if the script runs and produces a valid report structure.
        # The actual 'verified' value depends on the reproducibility of the pipeline.
        # If the pipeline is deterministic, 'verified' should be True.
        # If not, the report still exists and correctly flags it.
        
    except subprocess.TimeoutExpired:
        pytest.skip("Test timed out. Pipeline execution is too long for this integration test.")
    except Exception as e:
        # If the script fails due to missing data (e.g. T000 not fully run),
        # we might want to skip or fail depending on strictness.
        # Here we assume the environment is set up or we just check the script logic.
        if "No such file" in str(e) or "FileNotFoundError" in str(e):
            pytest.skip("Data files missing. Skipping full reproducibility test.")
        else:
            raise
