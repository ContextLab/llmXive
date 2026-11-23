"""
T022 Execution Wrapper
Runs the logistic regression fitting script (T022) and logs execution.
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def run_script(script_name, args=None):
    """
    Runs a specific script and logs the result.
    """
    cmd = [sys.executable, str(project_root / "code" / script_name)]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        elapsed = time.time() - start_time
        return {
            "status": "SUCCESS",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "elapsed_seconds": elapsed
        }
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        return {
            "status": "FAILED",
            "returncode": e.returncode,
            "stdout": e.stdout,
            "stderr": e.stderr,
            "elapsed_seconds": elapsed
        }

def main():
    print("Executing Model Fitting Phase...")
    
    log_entries = []
    
    # Step 1: Fit Logistic Regression (T022)
    # This script handles Null and Full models
    print("\n--- Step 1: Logistic Regression Fit (T022) ---")
    res_logistic = run_script("models/fit_logistic.py")
    log_entries.append({
        "step": "fit_logistic",
        "task_id": "T022",
        "result": res_logistic
    })
    
    # Step 2: Fit Bayesian Model (T025) - CPU only enforcement handled inside script
    # Note: T025 depends on T050 (CPU check). We run it here if T022 succeeded.
    if res_logistic["status"] == "SUCCESS":
        print("\n--- Step 2: Bayesian Model Fit (T025) ---")
        res_bayesian = run_script("models/fit_bayesian.py")
        log_entries.append({
            "step": "fit_bayesian",
            "task_id": "T025",
            "result": res_bayesian
        })
    else:
        log_entries.append({
            "step": "fit_bayesian",
            "task_id": "T025",
            "result": {"status": "SKIPPED", "reason": "Logistic fit failed"}
        })

    # Save Execution Log
    log_path = project_root / "data" / "model_fitting_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "executions": log_entries
        }, f, indent=2)
    
    print(f"\nModel fitting log saved to {log_path}")
    
    # Exit with error if critical steps failed
    if res_logistic["status"] == "FAILED":
        sys.exit(1)

if __name__ == "__main__":
    main()