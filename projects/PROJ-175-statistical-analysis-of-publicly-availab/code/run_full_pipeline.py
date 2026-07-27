import os
import sys
import json
import argparse
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_step(step_name, status, details=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "status": status,
        "details": details or {}
    }
    log_path = LOG_DIR / "pipeline_execution_log.json"
    
    logs = []
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    logs.append(log_entry)
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)
    print(f"[{status}] {step_name}")

def run_command(cmd, step_name):
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        log_step(step_name, "SUCCESS", {"stdout": result.stdout[:200]})
        return True
    except subprocess.CalledProcessError as e:
        log_step(step_name, "FAILED", {"stderr": e.stderr, "stdout": e.stdout})
        print(f"Error in {step_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run full research pipeline")
    parser.add_argument("--mode", choices=["full", "data", "models", "eval"], default="full",
                        help="Mode to run: full, data, models, or eval")
    args = parser.parse_args()

    start_time = time.time()
    
    # Map modes to steps
    steps = []
    if args.mode in ["full", "data"]:
        steps.extend([
            (["python", "code/data/download.py", "--dataset", "recipe1m", "--output", "data/raw/"], "Download Recipe1M"),
            (["python", "code/data/download.py", "--dataset", "ratings", "--output", "data/raw/"], "Download Ratings"),
            (["python", "code/data/preprocess.py", "--input", "data/raw/", "--output", "data/processed/"], "Preprocess Data"),
            (["python", "code/data/split.py", "--input", "data/processed/ingredient_pairs.csv", "--output", "data/processed/"], "Split Data"),
        ])
    
    if args.mode in ["full", "models"]:
        steps.extend([
            (["python", "code/models/fit_logistic.py", "--input", "data/processed/train.csv", "--output", "data/logs/"], "Fit Logistic"),
            (["python", "code/models/fit_bayesian.py", "--input", "data/processed/train.csv", "--output", "data/logs/"], "Fit Bayesian"),
        ])
    
    if args.mode in ["full", "eval"]:
        steps.extend([
            (["python", "code/evaluation/metrics.py", "--input", "data/processed/test.csv", "--output", "data/evaluation_metrics.json"], "Calculate Metrics"),
            (["python", "code/evaluation/capture_metrics.py", "--output", "data/evaluation_log.json"], "Capture Metrics"),
        ])

    failed_steps = []
    for cmd, name in steps:
        if not run_command(cmd, name):
            failed_steps.append(name)
            if args.mode == "full":
                print("Stopping pipeline due to failure.")
                break

    elapsed = time.time() - start_time
    
    # Final summary
    summary_path = DATA_DIR / "pipeline_execution_log.json"
    if summary_path.exists():
        with open(summary_path, 'r') as f:
            logs = json.load(f)
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "step": "SUMMARY",
            "status": "FAILED" if failed_steps else "SUCCESS",
            "details": {
                "elapsed_seconds": elapsed,
                "failed_steps": failed_steps
            }
        })
        with open(summary_path, 'w') as f:
            json.dump(logs, f, indent=2)
    
    if failed_steps:
        print(f"Pipeline failed. Steps failed: {failed_steps}")
        sys.exit(1)
    else:
        print(f"Pipeline completed successfully in {elapsed:.2f}s")
        sys.exit(0)

if __name__ == "__main__":
    main()
