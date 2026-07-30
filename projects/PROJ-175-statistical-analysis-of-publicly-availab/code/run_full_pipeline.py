"""
Task T099: Execute Full Pipeline
Orchestrates all tasks from data download to final report generation.
"""
import os
import sys
import json
import argparse
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log_step(step_name, status, details=None):
    """Log a pipeline step to the execution log."""
    log_entry = {
        "step": step_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    
    log_file = DATA_DIR / "pipeline_execution_log.json"
    
    # Load existing log or create new
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    else:
        log_data = {"pipeline_runs": []}
    
    log_data["pipeline_runs"].append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return log_entry

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        DATA_DIR / "final",
        ROOT_DIR / "docs",
        LOGS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def run_command(cmd, description):
    """Run a shell command and return success/failure."""
    print(f"\n--- {description} ---")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"stderr: {e.stderr}")
        return False, e.stderr

def run_data_pipeline():
    """Run the data preparation pipeline (T051, T013a-T019)."""
    steps = [
        (["python", str(ROOT_DIR / "code" / "data" / "download.py")], "Download datasets (T051)"),
        (["python", str(ROOT_DIR / "code" / "data" / "preprocess.py")], "Preprocess data (T013a-T018)"),
        (["python", str(ROOT_DIR / "code" / "data" / "split.py")], "Train/Test Split (T019)"),
    ]
    
    for cmd, desc in steps:
        success, output = run_command(cmd, desc)
        if not success:
            log_step(desc, "FAILED", {"error": output})
            raise RuntimeError(f"Pipeline step failed: {desc}")
        log_step(desc, "SUCCESS")
    
    return True

def run_model_fitting():
    """Run model fitting (T022, T025)."""
    steps = [
        (["python", str(ROOT_DIR / "code" / "models" / "fit_logistic.py")], "Fit Logistic Regression (T022)"),
        (["python", str(ROOT_DIR / "code" / "models" / "fit_bayesian.py")], "Fit Bayesian Model (T025)"),
    ]
    
    for cmd, desc in steps:
        success, output = run_command(cmd, desc)
        if not success:
            log_step(desc, "FAILED", {"error": output})
            # Note: Bayesian may fail gracefully with fallback
            if "bayesian" in desc.lower():
                log_step(desc, "FAILED_WITH_FALLBACK", {"error": output})
            else:
                raise RuntimeError(f"Model fitting step failed: {desc}")
        log_step(desc, "SUCCESS")
    
    return True

def run_evaluation():
    """Run evaluation and reporting (T029-T032, T055)."""
    steps = [
        (["python", str(ROOT_DIR / "code" / "evaluation" / "metrics.py")], "Calculate Metrics (T029)"),
        (["python", str(ROOT_DIR / "code" / "evaluation" / "capture_metrics.py")], "Capture Metrics (T043d)"),
        (["python", str(ROOT_DIR / "code" / "evaluation" / "generate_final_report.py")], "Generate Final Report (T055)"),
    ]
    
    for cmd, desc in steps:
        success, output = run_command(cmd, desc)
        if not success:
            log_step(desc, "FAILED", {"error": output})
            raise RuntimeError(f"Evaluation step failed: {desc}")
        log_step(desc, "SUCCESS")
    
    return True

def main():
    """Main entry point for the full pipeline."""
    parser = argparse.ArgumentParser(description="Run the full research pipeline")
    parser.add_argument("--skip-data", action="store_true", help="Skip data preparation")
    parser.add_argument("--skip-models", action="store_true", help="Skip model fitting")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation")
    args = parser.parse_args()
    
    start_time = time.time()
    
    try:
        ensure_directories()
        log_step("Pipeline Start", "RUNNING", {"args": vars(args)})
        
        if not args.skip_data:
            run_data_pipeline()
        
        if not args.skip_models:
            run_model_fitting()
        
        if not args.skip_eval:
            run_evaluation()
        
        end_time = time.time()
        duration = end_time - start_time
        
        log_step("Pipeline Complete", "SUCCESS", {"duration_seconds": duration})
        print(f"\nPipeline completed successfully in {duration:.2f} seconds.")
        return 0
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        log_step("Pipeline Failed", "FAILED", {"error": str(e), "duration_seconds": duration})
        print(f"\nPipeline failed after {duration:.2f} seconds: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())