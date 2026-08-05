"""
T099a_impl: Orchestration Implementation.
Executes the full pipeline in the correct order.
"""
import os
import sys
import json
import argparse
import time
import subprocess
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_step(step_name: str, status: str, details: str = ""):
    """Log a pipeline step."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "status": status,
        "details": details
    }
    logger.info(f"{step_name}: {status} - {details}")
    return log_entry

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
        (project_root.parent / d).mkdir(parents=True, exist_ok=True)

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        return False

def run_data_pipeline():
    """Run the data processing pipeline."""
    steps = [
        ("T012a_recipe1m", ["python", str(project_root / "data" / "download.py"), "--dataset", "recipe1m", "--output", str(project_root.parent / "data" / "raw")]),
        ("T013a_stream_recipe1m", ["python", str(project_root / "data" / "stream_recipe1m.py")]),
        ("T014_normalize", ["python", str(project_root / "data" / "preprocess.py")]),
        ("T015_co_occurrence", ["python", str(project_root / "data" / "co_occurrence.py")]),
        ("T016_similarity", ["python", str(project_root / "data" / "compute_similarity.py")]),
        ("T017_roles", ["python", str(project_root / "data" / "derive_roles.py")]),
        ("T018_impute", ["python", str(project_root / "data" / "impute_and_check.py")]),
        ("T019_labels", ["python", str(project_root / "data" / "derive_compatibility_labels.py")]),
        ("T013b_split", ["python", str(project_root / "data" / "split.py")])
    ]
    
    for step_name, cmd in steps:
        success = run_command(cmd, step_name)
        if not success:
            log_step(step_name, "FAILED", "Command execution failed")
            return False
        log_step(step_name, "SUCCESS")
    return True

def run_model_fitting():
    """Run the model fitting pipeline."""
    steps = [
        ("T023_vif", ["python", str(project_root / "models" / "diagnostics.py")]),
        ("T024_assumption", ["python", str(project_root / "models" / "fit_logistic.py"), "--input", str(project_root.parent / "data" / "processed" / "train.csv"), "--output", str(project_root.parent / "data" / "logs")]),
        ("T025_bayesian", ["python", str(project_root / "models" / "fit_bayesian.py"), "--input", str(project_root.parent / "data" / "processed" / "train.csv"), "--output", str(project_root.parent / "data" / "logs")])
    ]
    
    for step_name, cmd in steps:
        success = run_command(cmd, step_name)
        if not success:
            log_step(step_name, "FAILED", "Command execution failed")
            return False
        log_step(step_name, "SUCCESS")
    return True

def run_evaluation():
    """Run the evaluation pipeline."""
    steps = [
        ("T029_metrics", ["python", str(project_root / "evaluation" / "metrics.py")]),
        ("T030_calibration", ["python", str(project_root / "evaluation" / "report.py")]),
        ("T031_report", ["python", str(project_root / "evaluation" / "generate_final_report.py")])
    ]
    
    for step_name, cmd in steps:
        success = run_command(cmd, step_name)
        if not success:
            log_step(step_name, "FAILED", "Command execution failed")
            return False
        log_step(step_name, "SUCCESS")
    return True

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline.")
    parser.add_argument("--skip-data", action="store_true", help="Skip data processing")
    parser.add_argument("--skip-models", action="store_true", help="Skip model fitting")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation")
    args = parser.parse_args()
    
    ensure_directories()
    
    start_time = time.time()
    log_step("Pipeline Start", "RUNNING")
    
    success = True
    
    if not args.skip_data:
        if not run_data_pipeline():
            success = False
            log_step("Data Pipeline", "FAILED")
        else:
            log_step("Data Pipeline", "SUCCESS")
    
    if success and not args.skip_models:
        if not run_model_fitting():
            success = False
            log_step("Model Fitting", "FAILED")
        else:
            log_step("Model Fitting", "SUCCESS")
    
    if success and not args.skip_eval:
        if not run_evaluation():
            success = False
            log_step("Evaluation", "FAILED")
        else:
            log_step("Evaluation", "SUCCESS")
    
    end_time = time.time()
    duration = end_time - start_time
    
    log_step("Pipeline End", "SUCCESS" if success else "FAILED", f"Duration: {duration:.2f}s")
    
    # Save execution log
    log_path = project_root.parent / "data" / "pipeline_execution_log.json"
    with open(log_path, 'w') as f:
        json.dump({
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": duration,
            "status": "SUCCESS" if success else "FAILED"
        }, f, indent=2)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()