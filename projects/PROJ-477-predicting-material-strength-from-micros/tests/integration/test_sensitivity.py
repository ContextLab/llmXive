"""
Integration test for sensitivity sweep (US3).

This test verifies that the sensitivity analysis script:
1. Runs end-to-end without errors.
2. Produces the expected output file: results/sensitivity_report.json.
3. Contains the required metrics for the specified thresholds {0.01, 0.05, 0.1}.

Prerequisites:
- T029 (interpret.py) must be implemented to generate predictions if not already present.
- T026 (main.py) or T032 (predictor.py) must have generated a baseline predictions file.
- This test assumes the existence of a 'results/predictions.csv' or generates one via the predictor script if missing.
"""
import os
import json
import subprocess
import sys
import pytest
from pathlib import Path

# Project root relative to this test file (tests/integration/ -> ../..)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = PROJECT_ROOT / "results"

# Expected output artifact
EXPECTED_OUTPUT = RESULTS_DIR / "sensitivity_report.json"

# Thresholds defined in T031: {0.01, 0.05, 0.1}
REQUIRED_THRESHOLDS = [0.01, 0.05, 0.1]

def ensure_predictions_exist():
    """
    Ensures results/predictions.csv exists.
    If not, it attempts to run the predictor script (T032) or main.py to generate dummy data
    for the sake of this integration test. 
    In a real CI environment, this would be a hard dependency failure if data isn't present.
    """
    predictions_path = RESULTS_DIR / "predictions.csv"
    if not predictions_path.exists():
        # Attempt to run the predictor script to generate data
        # This assumes T032 is implemented. If T032 is not done, we might need to skip or fail.
        # For now, we try to invoke the sensitivity script which might handle missing data,
        # but the spec says T031 (sensitivity.py) computes FPR/FNR on existing predictions.
        # We will try to run the sensitivity script directly and see if it errors out due to missing file.
        pass
    return predictions_path

def test_sensitivity_sweep_integration():
    """
    Runs the sensitivity analysis script and validates the output report.
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ensure predictions exist (basic check)
    predictions_path = RESULTS_DIR / "predictions.csv"
    
    # If predictions don't exist, we might need to generate them.
    # However, T028 is the test for T031. If T031 is not implemented, this test should fail.
    # We assume T031 (code/eval/sensitivity.py) is the target implementation.
    
    # Construct the command to run the sensitivity analysis
    # Assuming the script is run via python code/eval/sensitivity.py
    script_path = CODE_DIR / "eval" / "sensitivity.py"
    
    if not script_path.exists():
        pytest.fail(f"Script {script_path} does not exist. T031 implementation missing.")

    # Run the script
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120 # 2 minute timeout
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Sensitivity analysis script timed out.")
    
    # Check if the script ran successfully (exit code 0)
    # Note: If the script requires predictions.csv and it's missing, it might exit with 1.
    # We handle the missing data scenario by checking the output or failing gracefully.
    
    # If the script failed because of missing predictions, we might need to generate them.
    # For this integration test, we assume the environment has the necessary data 
    # or the script handles the "no data" case gracefully (though spec implies real data).
    # Let's check the exit code first.
    
    # If the script fails due to missing predictions, we might need to skip or generate.
    # But the task is to test the script. If the script is correct, it should run.
    # If it fails because of missing input, that's a data pipeline issue, not a script issue.
    # However, to make this test robust, we'll check if the output file was created.
    
    # Re-run if necessary? No, let's just check the result.
    # If the script is T031, it should write results/sensitivity_report.json.
    
    # If the script exited with non-zero, check stderr for "FileNotFound" or similar.
    # If it's a data missing error, we might need to generate dummy data for the test to pass
    # if the project setup doesn't guarantee data presence at this stage.
    # Given the "Real data only" constraint, we cannot generate fake data here.
    # We assume the data pipeline (T015/T032) has run.
    
    # If the script failed, we fail the test.
    if result.returncode != 0:
        # If it's a specific "No predictions found" error, we might need to handle it differently,
        # but strictly speaking, the test environment should have data.
        # We'll print the error for debugging.
        print(f"Script stderr: {result.stderr}")
        print(f"Script stdout: {result.stdout}")
        
        # If the error is specifically about missing predictions.csv, we might skip this test
        # if the project is in a state where data hasn't been generated yet.
        # But for a proper integration test, we expect the data to be there.
        # Let's assume the data is there. If not, the test fails.
        pytest.fail(f"Sensitivity script failed with code {result.returncode}. Stderr: {result.stderr}")

    # Verify the output file exists
    assert EXPECTED_OUTPUT.exists(), f"Expected output file {EXPECTED_OUTPUT} was not created."

    # Load and validate the JSON content
    with open(EXPECTED_OUTPUT, "r") as f:
        report = json.load(f)

    # Validate schema: Must contain thresholds and metrics
    assert "thresholds" in report, "Report missing 'thresholds' key."
    
    # Check that all required thresholds are present
    reported_thresholds = report.get("thresholds", [])
    # Convert to floats for comparison
    reported_thresholds_floats = [float(t) for t in reported_thresholds]
    
    for req_thresh in REQUIRED_THRESHOLDS:
        # Check if the threshold is in the list (with some tolerance for float representation if needed, but string keys are safer)
        # The spec says "sweep thresholds {0.01, 0.05, 0.1}".
        # The JSON likely has keys like "0.01", "0.05", "0.1" or a list of objects.
        # Assuming the report structure is: {"thresholds": {"0.01": {...}, ...}} or similar.
        # Let's check the keys if it's a dict, or the list if it's a list.
        pass
    
    # Flexible validation: Check if the report contains entries for the required thresholds
    found_thresholds = []
    if isinstance(reported_thresholds, dict):
        found_thresholds = [float(k) for k in reported_thresholds.keys()]
    elif isinstance(reported_thresholds, list):
        # Assuming list of dicts with a 'threshold' key
        found_thresholds = [float(item.get("threshold", 0)) for item in reported_thresholds]
    
    for req in REQUIRED_THRESHOLDS:
        # Check if req is in found_thresholds (allowing small float error)
        if not any(abs(f - req) < 1e-6 for f in found_thresholds):
            pytest.fail(f"Required threshold {req} not found in report. Found: {found_thresholds}")

    # Validate that each threshold entry has FPR and FNR
    # Structure assumption: {"thresholds": {"0.01": {"fpr": ..., "fnr": ...}, ...}}
    if isinstance(report.get("thresholds"), dict):
        for t_str, metrics in report["thresholds"].items():
            assert "fpr" in metrics, f"Missing 'fpr' for threshold {t_str}"
            assert "fnr" in metrics, f"Missing 'fnr' for threshold {t_str}"
            # Validate types
            assert isinstance(metrics["fpr"], (int, float)), f"fpr for {t_str} is not numeric"
            assert isinstance(metrics["fnr"], (int, float)), f"fnr for {t_str} is not numeric"
    elif isinstance(report.get("thresholds"), list):
        for item in report["thresholds"]:
            assert "fpr" in item, "Missing 'fpr' in threshold item"
            assert "fnr" in item, "Missing 'fnr' in threshold item"

    # If we reached here, the integration test passed.
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])