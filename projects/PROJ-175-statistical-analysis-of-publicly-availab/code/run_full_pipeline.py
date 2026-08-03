import os
import sys
import json
import argparse
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure code directory is in path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

def log_step(step_name, status, duration=None, message=""):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "status": status,
        "duration_seconds": duration,
        "message": message
    }
    log_path = Path('data/pipeline_execution_log.json')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logs = []
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    
    logs.append(log_entry)
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)
    
    print(f"[{status}] {step_name}: {message}")

def ensure_directories():
    dirs = [
        'data/raw', 'data/processed', 'data/final', 'data/logs',
        'code/data', 'code/models', 'code/evaluation', 'code/validation'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_command(cmd, step_name):
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        duration = time.time() - start_time
        log_step(step_name, "SUCCESS", duration, "Completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        log_step(step_name, "FAILED", duration, f"Exit code: {e.returncode}, stderr: {e.stderr}")
        print(f"Error in {step_name}: {e.stderr}")
        return False

def run_data_pipeline():
    ensure_directories()
    steps = [
        (["python", "code/data/download.py", "--dataset", "recipe1m", "--output", "data/raw/"], "T013a_Recipe1M_Download"),
        (["python", "code/data/preprocess.py", "--input", "data/raw/", "--output", "data/processed/"], "T014_Normalization"),
        (["python", "code/data/split.py", "--input", "data/processed/ingredient_pairs.csv", "--output", "data/processed/"], "T018_Split"),
        # T019 is the current task
        (["python", "code/data/derive_compatibility_labels.py"], "T019_Compatibility_Labels")
    ]
    
    for cmd, name in steps:
        if not run_command(cmd, name):
            log_step("Pipeline_Data", "FAILED", message=f"Step {name} failed")
            return False
    log_step("Pipeline_Data", "SUCCESS", message="Data pipeline completed")
    return True

def run_model_fitting():
    ensure_directories()
    steps = [
        (["python", "code/models/fit_logistic.py", "--input", "data/processed/train.csv", "--output", "data/logs/"], "T023_Logistic_Fit"),
        (["python", "code/models/fit_bayesian.py", "--input", "data/processed/train.csv", "--output", "data/logs/"], "T025_Bayesian_Fit")
    ]
    
    for cmd, name in steps:
        if not run_command(cmd, name):
            log_step("Pipeline_Models", "FAILED", message=f"Step {name} failed")
            return False
    log_step("Pipeline_Models", "SUCCESS", message="Model fitting completed")
    return True

def run_evaluation():
    ensure_directories()
    steps = [
        (["python", "code/evaluation/metrics.py"], "T029_Evaluation"),
        (["python", "code/evaluation/capture_metrics.py"], "T029_Capture_Metrics")
    ]
    
    for cmd, name in steps:
        if not run_command(cmd, name):
            log_step("Pipeline_Evaluation", "FAILED", message=f"Step {name} failed")
            return False
    log_step("Pipeline_Evaluation", "SUCCESS", message="Evaluation completed")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the full statistical analysis pipeline.")
    parser.add_argument("--full", action="store_true", help="Run all stages")
    parser.add_argument("--data", action="store_true", help="Run only data pipeline")
    parser.add_argument("--models", action="store_true", help="Run only model fitting")
    parser.add_argument("--eval", action="store_true", help="Run only evaluation")
    args = parser.parse_args()

    success = True
    if args.full or (not args.data and not args.models and not args.eval):
        success = run_data_pipeline() and success
        if success:
            success = run_model_fitting() and success
        if success:
            success = run_evaluation() and success
    else:
        if args.data:
            success = run_data_pipeline() and success
        if args.models:
            success = run_model_fitting() and success
        if args.eval:
            success = run_evaluation() and success

    if success:
        print("Pipeline execution completed successfully.")
    else:
        print("Pipeline execution failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()