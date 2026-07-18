import os
import sys
import json
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.metrics import main as run_metrics
from evaluation.report import main as run_report

def run_evaluation_step(step_name, step_func):
    """
    Executes a specific evaluation step, timing it and handling errors.
    """
    start_time = time.time()
    try:
        print(f"Starting {step_name}...")
        step_func()
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"{step_name} completed successfully in {elapsed:.2f} seconds.")
        return {
            "step": step_name,
            "status": "SUCCESS",
            "duration_seconds": elapsed
        }
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        error_msg = str(e)
        print(f"{step_name} FAILED after {elapsed:.2f} seconds: {error_msg}")
        return {
            "step": step_name,
            "status": "FAILED",
            "duration_seconds": elapsed,
            "error": error_msg
        }

def main():
    """
    Executes the full evaluation pipeline (Metrics + Report Generation)
    and writes the execution log to data/evaluation_log.json.
    """
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline": "Evaluation",
        "steps": [],
        "overall_status": "SUCCESS"
    }

    try:
        # Step 1: Calculate Metrics (AUC, Calibration, etc.)
        # This corresponds to T029
        metrics_result = run_evaluation_step("metrics_calculation", run_metrics)
        log_data["steps"].append(metrics_result)

        if metrics_result["status"] == "FAILED":
            log_data["overall_status"] = "FAILED"
            # Continue to attempt report generation if possible, or fail immediately
            # Based on strict dependencies, if metrics fail, report might fail too.
            # We log the failure and proceed to catch-up logic or final status.
        
        # Step 2: Generate Report (Statistical Tests, Final Summary)
        # This corresponds to T030, T031, T032, T055
        report_result = run_evaluation_step("report_generation", run_report)
        log_data["steps"].append(report_result)

        if report_result["status"] == "FAILED":
            log_data["overall_status"] = "FAILED"

        # Determine final status based on step results
        if any(step["status"] == "FAILED" for step in log_data["steps"]):
            log_data["overall_status"] = "FAILED"
        else:
            log_data["overall_status"] = "SUCCESS"

    except Exception as e:
        log_data["overall_status"] = "FAILED"
        log_data["unexpected_error"] = str(e)

    # Write the log file
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    log_path = data_dir / "evaluation_log.json"
    
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Evaluation log written to {log_path}")
    
    # Exit with non-zero code if failed
    if log_data["overall_status"] == "FAILED":
        sys.exit(1)

if __name__ == "__main__":
    main()