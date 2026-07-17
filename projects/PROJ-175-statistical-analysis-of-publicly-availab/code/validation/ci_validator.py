"""
CI Validation Script for PROJ-175.

Executes the full pipeline as described in quickstart.md and measures
the total wall-clock time to ensure it completes within the 6-hour limit.

Deliverable: data/ci_validation_report.json
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
REPORT_PATH = DATA_DIR / "ci_validation_report.json"

# Time limit in seconds (6 hours)
TIME_LIMIT_SECONDS = 6 * 60 * 60

def run_pipeline_step(step_name, script_path, args=None):
    """Run a single pipeline step and return success status and duration."""
    print(f"\n{'='*60}")
    print(f"Running: {step_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        # Run the script, capturing output
        result = subprocess.run(
            cmd,
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT_SECONDS # Fail if individual step takes too long
        )
        
        duration = time.time() - start_time
        
        if result.returncode != 0:
            print(f"FAILED: {step_name}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False, duration, result.stderr
        
        print(f"SUCCESS: {step_name} (Duration: {duration:.2f}s)")
        return True, duration, None
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"TIMEOUT: {step_name} exceeded {TIME_LIMIT_SECONDS}s limit")
        return False, duration, "Timeout"
    except Exception as e:
        duration = time.time() - start_time
        print(f"ERROR: {step_name} - {str(e)}")
        return False, duration, str(e)

def main():
    print("Starting CI Validation Pipeline...")
    print(f"Time Limit: {TIME_LIMIT_SECONDS / 3600:.2f} hours")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define the pipeline steps based on quickstart.md logic
    # We assume the scripts are designed to be run sequentially to produce the final output
    steps = [
        ("Data Verification", "data/verify.py", ["verify_data_sources"]),
        ("Data Download", "data/download.py", ["download_datasets"]),
        ("Data Preprocessing", "data/preprocess.py", ["main"]),
        ("Data Splitting", "data/split.py", ["create_train_test_split"]),
        ("Power Analysis (Logistic)", "models/diagnostics.py", ["power_analysis_logistic"]),
        ("Power Analysis (Bayesian)", "models/diagnostics.py", ["power_analysis_bayesian"]),
        ("Model Fitting (Logistic)", "models/fit_logistic.py", ["main"]),
        ("Model Fitting (Bayesian)", "models/fit_bayesian.py", ["main"]),
        ("Model Diagnostics", "models/diagnostics.py", ["main"]),
        ("Evaluation Metrics", "evaluation/metrics.py", ["main"]),
        ("Report Generation", "evaluation/report.py", ["main"]),
    ]
    
    total_start = time.time()
    results = []
    all_passed = True
    
    for step_name, script_rel_path, args in steps:
        script_path = CODE_DIR / script_rel_path
        
        if not script_path.exists():
            print(f"WARNING: Script not found: {script_path}. Skipping.")
            results.append({
                "step": step_name,
                "status": "skipped",
                "duration_seconds": 0,
                "error": "Script not found"
            })
            continue
        
        success, duration, error = run_pipeline_step(step_name, script_path, args)
        
        results.append({
            "step": step_name,
            "status": "passed" if success else "failed",
            "duration_seconds": round(duration, 2),
            "error": error
        })
        
        if not success:
            all_passed = False
            # Depending on strictness, we might stop here. 
            # For validation, we continue to see total time if possible, 
            # but the overall result will be failed.
            # However, if a critical step fails, the pipeline is broken.
            # We'll break to save time if a critical step fails.
            print(f"CRITICAL FAILURE in {step_name}. Stopping pipeline.")
            break
    
    total_duration = time.time() - total_start
    passed = all_passed and (total_duration <= TIME_LIMIT_SECONDS)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "time_limit_seconds": TIME_LIMIT_SECONDS,
        "total_duration_seconds": round(total_duration, 2),
        "passed": passed,
        "steps": results
    }
    
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE")
    print(f"Total Duration: {total_duration:.2f}s ({total_duration/3600:.2f}h)")
    print(f"Time Limit: {TIME_LIMIT_SECONDS}s ({TIME_LIMIT_SECONDS/3600:.2f}h)")
    print(f"Result: {'PASSED' if passed else 'FAILED'}")
    print(f"Report saved to: {REPORT_PATH}")
    print(f"{'='*60}")
    
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main())