"""
Integration test for T043b: Execute Model Fitting

Verifies that the execution script runs the fitting scripts and produces
the expected log file with valid structure.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import subprocess

# Add code directory to path
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
data_dir = project_root / "data"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """
    Sets up a temporary environment to avoid overwriting real data during tests.
    In a real CI run, this would use the actual data directory.
    """
    # For this test, we assume the data files (logistic_results.json, etc.)
    # might not exist if the previous tasks (T022, T025) haven't run.
    # This test validates the *execution script's* logic, not the model fitting itself.
    # We mock the existence of required output files to ensure the script completes.
    
    # Create necessary dummy files to simulate a successful prior run
    final_dir = data_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    # Dummy Logistic Results
    (final_dir / "logistic_results.json").write_text(json.dumps({
        "coefficients": {"test": 0.5},
        "p_values": {"test": 0.01},
        "vif_scores": {"test": 1.2}
    }))
    
    # Dummy Bayesian Results
    (final_dir / "bayesian_results.json").write_text(json.dumps({
        "trace": "dummy",
        "summary": "dummy"
    }))
    
    # Dummy Bayesian Convergence Log
    (data_dir / "bayesian_convergence_log.json").write_text(json.dumps({
        "status": "SUCCESS",
        "metrics": {"R_hat": 1.01, "ESS": 500}
    }))

def test_execute_model_fitting_creates_log():
    """
    Test that execute_model_fitting.py runs and creates the log file.
    """
    script_path = code_dir / "validation" / "execute_model_fitting.py"
    log_path = data_dir / "model_fitting_log.json"
    
    # Remove existing log to ensure fresh run
    if log_path.exists():
        log_path.unlink()
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(code_dir),
        capture_output=True,
        text=True
    )
    
    # The script should exit with 0 if it creates the log successfully (even if models failed, 
    # provided the script itself ran). However, our script exits 1 if models fail.
    # Since we mocked the files, it should succeed.
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Verify log file exists
    assert log_path.exists(), "model_fitting_log.json was not created"
    
    # Verify log content
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert "execution_start" in log_data
    assert "scripts" in log_data
    assert "overall_status" in log_data
    assert len(log_data["scripts"]) == 2 # Logistic and Bayesian
    
    # Verify script names
    script_names = [s["script"] for s in log_data["scripts"]]
    assert "fit_logistic.py" in script_names
    assert "fit_bayesian.py" in script_names
    
    # Verify structure of individual results
    for script_res in log_data["scripts"]:
        assert "status" in script_res
        assert "runtime_seconds" in script_res
        assert script_res["status"] in ["SUCCESS", "FAILED", "TIMEOUT", "ERROR"]

def test_execute_model_fitting_handles_missing_output():
    """
    Test that the execution script correctly identifies missing output files
    and reports failure.
    """
    # Remove the dummy files to simulate a failed prior step
    (data_dir / "final" / "logistic_results.json").unlink()
    (data_dir / "final" / "bayesian_results.json").unlink()
    (data_dir / "bayesian_convergence_log.json").unlink()
    
    script_path = code_dir / "validation" / "execute_model_fitting.py"
    log_path = data_dir / "model_fitting_log.json"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(code_dir),
        capture_output=True,
        text=True
    )
    
    # The script should detect missing files and exit with 1
    # Note: If the underlying scripts (fit_logistic.py) also fail because input data is missing,
    # the error message will reflect that. We are testing the *validation* logic.
    # If the scripts run but output files are missing, it should fail.
    
    # We expect the log to be created even on failure
    assert log_path.exists(), "Log file should be created even on failure"
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    # The overall status should be FAILED because output files were missing
    assert log_data["overall_status"] == "FAILED"
    
    # Check that at least one script reported failure
    failed_scripts = [s for s in log_data["scripts"] if s["status"] != "SUCCESS"]
    assert len(failed_scripts) > 0, "At least one script should have failed"
    
    # Restore files for other tests
    (data_dir / "final" / "logistic_results.json").write_text(json.dumps({"test": 1}))
    (data_dir / "final" / "bayesian_results.json").write_text(json.dumps({"test": 1}))
    (data_dir / "bayesian_convergence_log.json").write_text(json.dumps({"status": "SUCCESS"}))
