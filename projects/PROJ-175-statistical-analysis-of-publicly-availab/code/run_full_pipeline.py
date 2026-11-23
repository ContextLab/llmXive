import os
import sys
import json
import argparse
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/pipeline_execution_log.json'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_step(step_name, status, details=None):
    """Log a pipeline step to the execution log."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "status": status,
        "details": details or {}
    }
    
    log_file = Path("data/pipeline_execution_log.json")
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = [logs]
        except json.JSONDecodeError:
            logs = []
    
    logs.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.info(f"{status}: {step_name}")

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/final",
        "data/logs",
        "docs",
        "code/data",
        "code/models",
        "code/evaluation"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def run_command(cmd, description=""):
    """Run a shell command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Success: {description}")
        if result.stdout:
            logger.debug(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        return False

def run_data_pipeline():
    """Run the data processing pipeline."""
    logger.info("Starting data pipeline...")
    
    # Step 1: Download datasets
    success = run_command(
        ["python", "code/data/download.py", "--dataset", "recipe1m", "--output", "data/raw/"],
        "Download Recipe1M dataset"
    )
    if not success:
        log_step("download", "FAILED", {"error": "Dataset download failed"})
        return False
    log_step("download", "SUCCESS")
    
    # Step 2: Preprocess data
    success = run_command(
        ["python", "code/data/preprocess.py", "--input", "data/raw/", "--output", "data/processed/"],
        "Preprocess data"
    )
    if not success:
        log_step("preprocess", "FAILED", {"error": "Preprocessing failed"})
        return False
    log_step("preprocess", "SUCCESS")
    
    # Step 3: Split data
    success = run_command(
        ["python", "code/data/split.py", "--input", "data/processed/ingredient_pairs.csv", "--output", "data/processed/"],
        "Split data into train/test"
    )
    if not success:
        log_step("split", "FAILED", {"error": "Data split failed"})
        return False
    log_step("split", "SUCCESS")
    
    return True

def run_model_fitting():
    """Run model fitting scripts."""
    logger.info("Starting model fitting...")
    
    # Step 1: Fit logistic regression
    success = run_command(
        ["python", "code/models/fit_logistic.py", "--input", "data/processed/train.csv", "--output", "data/logs/"],
        "Fit logistic regression model"
    )
    if not success:
        log_step("fit_logistic", "FAILED", {"error": "Logistic fitting failed"})
        return False
    log_step("fit_logistic", "SUCCESS")
    
    # Step 2: Fit Bayesian model
    success = run_command(
        ["python", "code/models/fit_bayesian.py", "--input", "data/processed/train.csv", "--output", "data/logs/"],
        "Fit Bayesian model"
    )
    if not success:
        log_step("fit_bayesian", "FAILED", {"error": "Bayesian fitting failed"})
        return False
    log_step("fit_bayesian", "SUCCESS")
    
    return True

def run_evaluation():
    """Run evaluation and generate metrics."""
    logger.info("Starting evaluation...")
    
    # Step 1: Calculate metrics and generate calibration plot
    success = run_command(
        ["python", "code/evaluation/metrics.py"],
        "Calculate evaluation metrics and generate calibration plot"
    )
    if not success:
        log_step("evaluation", "FAILED", {"error": "Evaluation failed"})
        return False
    log_step("evaluation", "SUCCESS")
    
    # Step 2: Capture all metrics for final report
    success = run_command(
        ["python", "code/evaluation/capture_metrics.py"],
        "Capture all metrics for final report"
    )
    if not success:
        log_step("capture_metrics", "FAILED", {"error": "Metric capture failed"})
        return False
    log_step("capture_metrics", "SUCCESS")
    
    # Step 3: Generate final report
    success = run_command(
        ["python", "code/evaluation/generate_final_report.py"],
        "Generate final report"
    )
    if not success:
        log_step("generate_report", "FAILED", {"error": "Report generation failed"})
        return False
    log_step("generate_report", "SUCCESS")
    
    return True

def main():
    """Main pipeline orchestration."""
    parser = argparse.ArgumentParser(description="Run the full statistical analysis pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Skip data download")
    parser.add_argument("--skip-models", action="store_true", help="Skip model fitting")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation")
    args = parser.parse_args()
    
    ensure_directories()
    log_step("pipeline_start", "INITIALIZED", {"args": vars(args)})
    
    # Data pipeline
    if not args.skip_download:
        if not run_data_pipeline():
            log_step("pipeline_end", "FAILED", {"reason": "Data pipeline failed"})
            return 1
    
    # Model fitting
    if not args.skip_models:
        if not run_model_fitting():
            log_step("pipeline_end", "FAILED", {"reason": "Model fitting failed"})
            return 1
    
    # Evaluation
    if not args.skip_eval:
        if not run_evaluation():
            log_step("pipeline_end", "FAILED", {"reason": "Evaluation failed"})
            return 1
    
    log_step("pipeline_end", "SUCCESS")
    logger.info("Pipeline completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
