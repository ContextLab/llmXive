"""
Integration test for T063a: Verify 6-Hour Constraint.
"""
import os
import json
import subprocess
import sys
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

def test_verify_streaming_performance_script_runs():
    """
    Tests that the verify_streaming_performance.py script runs successfully
    and produces the required output artifact.
    """
    output_file = DATA_RESULTS_DIR / "streaming_performance_report.json"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the script
    script_path = CODE_DIR / "verify_streaming_performance.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # Assert script exited successfully (or with expected exit code 0)
    # Note: If it fails due to time, it exits 1, but for a small N it should pass.
    # We expect exit code 0 for a successful constraint check.
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Assert output file exists
    assert output_file.exists(), f"Output file {output_file} was not created"
    
    # Assert output file is valid JSON and contains required keys
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    assert "status" in report, "Missing 'status' key in report"
    assert "timing" in report, "Missing 'timing' key in report"
    assert "total_estimated_time_s" in report["timing"], "Missing 'total_estimated_time_s' in timing"
    assert "target_limit_s" in report["timing"], "Missing 'target_limit_s' in timing"
    assert report["status"] in ["PASS", "FAIL"], f"Invalid status: {report['status']}"
    
    # Assert that the estimated time is a number
    assert isinstance(report["timing"]["total_estimated_time_s"], (int, float))

def test_verify_streaming_performance_report_structure():
    """
    Validates the structure of the generated report against the T063a specification.
    """
    output_file = DATA_RESULTS_DIR / "streaming_performance_report.json"
    if not output_file.exists():
        # If the file doesn't exist, run the test first
        test_verify_streaming_performance_script_runs()
    
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    # Verify specific fields required by T063a
    assert "task_id" in report and report["task_id"] == "T063a"
    assert "parameters" in report
    assert "simulated_samples" in report["parameters"]
    assert report["parameters"]["simulated_samples"] > 1000, "Simulated samples must be > 1000"
    
    # Verify timing breakdown
    timing = report["timing"]
    assert "streaming_phase_measured_s" in timing
    assert "analysis_phase_measured_s" in timing
    assert "estimated_streaming_time_s" in timing
    assert "estimated_analysis_time_s" in timing
    assert "total_estimated_time_s" in timing
    assert "target_limit_s" in timing
    
    # Verify the target limit is 6 hours (21600 seconds)
    assert timing["target_limit_s"] == 21600, "Target limit must be 6 hours (21600s)"

if __name__ == "__main__":
    test_verify_streaming_performance_script_runs()
    test_verify_streaming_performance_report_structure()
    print("All tests passed.")
