import os
import sys
import json
import time
import subprocess
from pathlib import Path

def run_script(script_name: str, args: list = None) -> dict:
    """
    Runs a specific Python script and captures the output and timing.
    Returns a dict with status, runtime, and output/error logs.
    """
    start_time = time.time()
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)

    try:
        # Run the script, capturing stdout and stderr
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout for model fitting
            check=False
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            return {
                "status": "SUCCESS",
                "runtime_seconds": elapsed_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {
                "status": "FAILED",
                "runtime_seconds": elapsed_time,
                "error": result.stderr,
                "exit_code": result.returncode
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "runtime_seconds": 3600,
            "error": "Script execution timed out after 1 hour"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "runtime_seconds": time.time() - start_time,
            "error": str(e)
        }

def main():
    """
    Orchestrates the model fitting execution (Logistic and Bayesian).
    Writes results to data/model_fitting_log.json.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    models_dir = project_root / "code" / "models"
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tasks": {},
        "overall_status": "PENDING"
    }
    
    scripts_to_run = [
        ("Logistic Regression", "models/fit_logistic.py"),
        ("Bayesian Model", "models/fit_bayesian.py")
    ]
    
    for task_name, script_path in scripts_to_run:
        full_script_path = models_dir / script_path
        
        if not full_script_path.exists():
            log["tasks"][task_name] = {
                "status": "SKIPPED",
                "reason": f"Script not found: {script_path}"
            }
            continue
        
        print(f"Running {task_name}...")
        result = run_script(str(full_script_path))
        
        # Check convergence status from the script output if available
        convergence_status = "UNKNOWN"
        if task_name == "Bayesian Model":
            # Try to read convergence status from the generated log if it exists
            bayes_log_path = data_dir / "bayesian_convergence_log.json"
            if bayes_log_path.exists():
                try:
                    with open(bayes_log_path, 'r') as f:
                        bayes_data = json.load(f)
                        convergence_status = bayes_data.get("status", "UNKNOWN")
                except (json.JSONDecodeError, IOError):
                    pass
        
        log["tasks"][task_name] = {
            "status": result["status"],
            "runtime_seconds": result["runtime_seconds"],
            "convergence_status": convergence_status,
            "details": result.get("error", "Success") if result["status"] != "SUCCESS" else None
        }
    
    # Determine overall status
    all_success = all(
        t["status"] == "SUCCESS" 
        for t in log["tasks"].values() 
        if t["status"] not in ["SKIPPED"]
    )
    
    if all_success:
        log["overall_status"] = "SUCCESS"
    elif any(t["status"] == "TIMEOUT" for t in log["tasks"].values()):
        log["overall_status"] = "TIMEOUT"
    else:
        log["overall_status"] = "FAILED"
    
    # Write the log file
    output_path = data_dir / "model_fitting_log.json"
    with open(output_path, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"Model fitting log written to {output_path}")
    print(f"Overall Status: {log['overall_status']}")
    
    if log["overall_status"] != "SUCCESS":
        sys.exit(1)

if __name__ == "__main__":
    main()