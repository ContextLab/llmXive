"""
Orchestrator for the Statistical Analysis of Recipe Data pipeline.
Executes data download, preprocessing, model fitting, and evaluation.
"""
import os
import sys
import json
import argparse
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure we can import from the code directory
CODE_DIR = Path(__file__).parent
sys.path.insert(0, str(CODE_DIR))

def log_step(log_file: Path, step_name: str, status: str, message: str = ""):
    """Log a step to the execution log file."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "step": step_name,
        "status": status,
        "message": message
    }
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    
    logs.append(log_entry)
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/final",
        "data/logs",
        "docs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_command(cmd: list, log_file: Path, step_name: str) -> bool:
    """Run a command and log the result."""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        log_step(log_file, step_name, "SUCCESS", "Completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with return code {e.returncode}. Stderr: {e.stderr}"
        log_step(log_file, step_name, "FAILED", error_msg)
        print(f"ERROR: {error_msg}", file=sys.stderr)
        return False
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_step(log_file, step_name, "FAILED", error_msg)
        print(f"ERROR: {error_msg}", file=sys.stderr)
        return False

def run_data_pipeline(log_file: Path) -> bool:
    """Execute the data download and preprocessing pipeline."""
    print("=== Starting Data Pipeline ===")
    
    # Step 1: Verify data sources (T012)
    if not run_command(
        [sys.executable, "code/data/verify.py"],
        log_file, "verify_data_sources"
    ):
        return False

    # Step 2: Download datasets (T051, T013)
    if not run_command(
        [sys.executable, "code/data/download.py", "--dataset", "recipe1m", "--output", "data/raw"],
        log_file, "download_recipe1m"
    ):
        return False

    # Step 3: Preprocess data (T014, T014c, T015, T016, T017)
    if not run_command(
        [sys.executable, "code/data/preprocess.py", "--input", "data/raw", "--output", "data/processed"],
        log_file, "preprocess_data"
    ):
        return False

    # Step 4: Compute embeddings and similarity (T014c, T016)
    if not run_command(
        [sys.executable, "code/data/compute_similarity.py"],
        log_file, "compute_similarity"
    ):
        return False

    # Step 5: Derive roles (T017)
    if not run_command(
        [sys.executable, "code/data/derive_roles.py"],
        log_file, "derive_roles"
    ):
        return False

    # Step 6: Split data (T019)
    if not run_command(
        [sys.executable, "code/data/split.py", "--input", "data/processed", "--output", "data/processed"],
        log_file, "split_data"
    ):
        return False

    print("=== Data Pipeline Completed ===")
    return True

def run_model_fitting(log_file: Path) -> bool:
    """Execute model fitting (logistic and Bayesian)."""
    print("=== Starting Model Fitting ===")
    
    # Step 1: Calculate VIF (T023)
    if not run_command(
        [sys.executable, "code/models/diagnostics.py", "--action", "vif"],
        log_file, "calculate_vif"
    ):
        return False

    # Step 2: Fit logistic regression (T022)
    if not run_command(
        [sys.executable, "code/models/fit_logistic.py", "--input", "data/processed", "--output", "data/final"],
        log_file, "fit_logistic"
    ):
        return False

    # Step 3: Fit Bayesian model (T025)
    if not run_command(
        [sys.executable, "code/models/fit_bayesian.py", "--input", "data/processed", "--output", "data/final"],
        log_file, "fit_bayesian"
    ):
        return False

    print("=== Model Fitting Completed ===")
    return True

def run_evaluation(log_file: Path) -> bool:
    """Execute evaluation and report generation."""
    print("=== Starting Evaluation ===")
    
    # Step 1: Calculate metrics (T029)
    if not run_command(
        [sys.executable, "code/evaluation/metrics.py", "--input", "data/final", "--output", "data/evaluation_metrics.json"],
        log_file, "calculate_metrics"
    ):
        return False

    # Step 2: Capture all metrics (T043d)
    if not run_command(
        [sys.executable, "code/evaluation/capture_metrics.py"],
        log_file, "capture_metrics"
    ):
        return False

    # Step 3: Generate final report (T044)
    if not run_command(
        [sys.executable, "code/evaluation/generate_final_report.py"],
        log_file, "generate_report"
    ):
        return False

    print("=== Evaluation Completed ===")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the full statistical analysis pipeline")
    parser.add_argument("--mode", choices=["full", "data", "models", "eval"], default="full",
                      help="Which part of the pipeline to run")
    args = parser.parse_args()

    log_file = Path("data/pipeline_execution_log.json")
    ensure_directories()

    success = True
    
    if args.mode in ["full", "data"]:
        success = run_data_pipeline(log_file) and success
    
    if args.mode in ["full", "models"] and success:
        success = run_model_fitting(log_file) and success
    
    if args.mode in ["full", "eval"] and success:
        success = run_evaluation(log_file) and success

    if success:
        print("Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("Pipeline failed. Check data/pipeline_execution_log.json for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()