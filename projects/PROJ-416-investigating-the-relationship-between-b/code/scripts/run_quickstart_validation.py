import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime

from code.config import Config

def log_section(title: str):
    """Log a section header."""
    logging.info("=" * 60)
    logging.info(f" {title} ")
    logging.info("=" * 60)

def check_file_exists(path: Path, required: bool = True) -> bool:
    """Check if a file exists."""
    exists = path.exists()
    if required and not exists:
        logging.error(f"Required file missing: {path}")
    elif exists:
        logging.info(f"Found: {path}")
    return exists

def run_pipeline_step(stage: str) -> bool:
    """Run a pipeline stage and return success status."""
    cmd = [sys.executable, "code/main.py", "--stage", stage]
    logging.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Stage {stage} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Stage {stage} failed with code {e.returncode}")
        logging.error(f"stderr: {e.stderr}")
        return False

def validate_outputs():
    """Validate that all required outputs exist."""
    log_section("Validating Outputs")
    
    required_files = [
        Config.DATA_METRICS / "qc_metrics.csv",
        Config.DATA_METRICS / "network_metrics.csv",
        Config.DATA_METRICS / "statistical_results.csv",
        Config.DATA_METRICS / "power_analysis.json",
        Config.REPORTS_DIR / "sensitivity_analysis.md",
        Config.REPORTS_DIR / "results.md"
    ]
    
    all_exist = True
    for f in required_files:
        if not check_file_exists(f, required=True):
            all_exist = False
    
    return all_exist

def main():
    """Run the full quickstart validation pipeline."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    log_section("Starting Quickstart Validation")
    
    # Ensure directories
    Config.ensure_directories()
    
    # Run pipeline stages
    stages = ["download", "validate", "preprocess", "save_metadata", 
              "compute", "validate_metrics", "analyze", "report", "save_stats"]
    
    success = True
    for stage in stages:
        if not run_pipeline_step(stage):
            logging.error(f"Pipeline failed at stage: {stage}")
            success = False
            break
    
    if success:
        # Validate outputs
        if validate_outputs():
            log_section("Quickstart Validation PASSED")
            logging.info("All stages completed and outputs validated.")
        else:
            log_section("Quickstart Validation FAILED")
            logging.error("Some required outputs are missing.")
            success = False
    else:
        log_section("Quickstart Validation FAILED")
        logging.error("Pipeline execution failed.")
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()