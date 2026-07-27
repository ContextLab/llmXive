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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR

def run_script():
    """Execute the logistic regression fitting script."""
    script_path = PROJECT_ROOT / "code" / "models" / "fit_logistic.py"
    output_log_path = LOGS_DIR / "model_fitting_log.json"

    start_time = time.time()
    status = "SUCCESS"
    error_msg = None

    try:
        # Check memory limit before running
        # We assume the script itself handles memory checks, but we log here too
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode != 0:
            status = "FAILED"
            error_msg = result.stderr
            print(f"Script failed with return code {result.returncode}")
            print(f"Error: {error_msg}")
        else:
            print("Script executed successfully")
            print(result.stdout)

    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        print(f"Exception occurred: {e}")

    end_time = time.time()
    duration = end_time - start_time

    log_entry = {
        "task_id": "T022",
        "status": status,
        "duration_seconds": duration,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "script_path": str(script_path),
        "error": error_msg
    }

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)

    print(f"Log saved to {output_log_path}")

    if status == "FAILED":
        sys.exit(1)

def main():
    run_script()

if __name__ == "__main__":
    main()