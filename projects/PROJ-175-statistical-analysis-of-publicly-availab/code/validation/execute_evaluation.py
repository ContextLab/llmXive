"""
Task T043c: Execute Evaluation
Runs the evaluation and reporting scripts on the CI runner.
Produces data/evaluation_log.json with runtime and success status.
"""
import os
import sys
import json
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from evaluation.metrics import main as run_metrics
from evaluation.report import main as run_report

def run_evaluation_step():
    """
    Executes the full evaluation pipeline:
    1. Calculate metrics (AUC, Precision, Recall, Calibration)
    2. Perform statistical comparison (Bootstrap/Permutation)
    3. Generate draft final report
    """
    log_data = {
        "status": "SUCCESS",
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "end_time": None,
        "runtime_seconds": 0.0,
        "artifacts_created": [],
        "errors": []
    }

    start_time = time.time()
    try:
        # Step 1: Run Metrics Calculation
        # This script reads model predictions and test data to generate
        # data/evaluation_metrics.json and data/calibration_test_results.json
        print("Starting metrics calculation...")
        run_metrics()
        log_data["artifacts_created"].append("data/evaluation_metrics.json")
        log_data["artifacts_created"].append("data/calibration_test_results.json")
        print("Metrics calculation completed.")

        # Step 2: Run Statistical Comparison and Report Generation
        # This script reads metrics, performs bootstrap test, and generates
        # data/auc_delta_metrics.json and docs/draft_final_report.md
        print("Starting statistical comparison and report generation...")
        run_report()
        log_data["artifacts_created"].append("data/auc_delta_metrics.json")
        log_data["artifacts_created"].append("docs/draft_final_report.md")
        print("Statistical comparison and report generation completed.")

    except Exception as e:
        log_data["status"] = "FAILED"
        log_data["errors"].append(str(e))
        import traceback
        log_data["errors"].append(traceback.format_exc())
        print(f"Evaluation failed: {e}")
        raise
    finally:
        end_time = time.time()
        log_data["end_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        log_data["runtime_seconds"] = round(end_time - start_time, 2)

    return log_data

def main():
    """Main entry point for T043c."""
    output_path = project_root / "data" / "evaluation_log.json"
    
    # Ensure data directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Executing Evaluation Pipeline (T043c)...")
    try:
        log_data = run_evaluation_step()
        
        # Write log to disk
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"Evaluation log written to: {output_path}")
        print(f"Status: {log_data['status']}")
        print(f"Runtime: {log_data['runtime_seconds']}s")
        
        if log_data["status"] == "FAILED":
            print(f"Errors: {log_data['errors']}")
            sys.exit(1)
            
    except Exception as e:
        # Write failure log even if the step crashes before completion
        error_log = {
            "status": "FAILED",
            "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "end_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "runtime_seconds": 0.0,
            "artifacts_created": [],
            "errors": [str(e)]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, indent=2)
        print(f"Critical failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()