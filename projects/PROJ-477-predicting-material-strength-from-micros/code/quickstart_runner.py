"""
Quickstart runner for PROJ-477.
Executes the full pipeline (download, preprocess, split, validate, train, evaluate)
and logs the output to results/quickstart_validation.log.
"""
import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path if running from root, or adjust based on structure
# Assuming this script is run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = RESULTS_DIR / "quickstart_validation.log"

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> bool:
    """Run a command and log the result."""
    logger.info(f"--- {description} ---")
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(CODE_DIR),
            check=True,
            capture_output=False,
            text=True
        )
        logger.info(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Return code: {e.returncode}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return False

def main():
    logger.info("Starting Quickstart Validation for PROJ-477")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Results Dir: {RESULTS_DIR}")
    logger.info(f"Log File: {LOG_FILE}")

    start_time = datetime.now()
    logger.info(f"Start Time: {start_time.isoformat()}")

    # Step 1: Data Processing (Download -> Preprocess -> Split -> Validate)
    # Using process_all.py which orchestrates the data pipeline
    success = run_command(
        [sys.executable, "data/process_all.py"],
        "Step 1: Data Pipeline (Download, Preprocess, Split, Validate)"
    )
    if not success:
        logger.error("Data pipeline failed. Stopping quickstart.")
        finish_time = datetime.now()
        summary = {
            "status": "failed",
            "step_failed": "Data Pipeline",
            "start_time": start_time.isoformat(),
            "end_time": finish_time.isoformat(),
            "duration_seconds": (finish_time - start_time).total_seconds()
        }
        with open(RESULTS_DIR / "quickstart_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        return 1

    # Step 2: Model Training and Evaluation
    # Using main.py which handles training and evaluation
    # Note: Using --no-augmentation for faster quickstart if needed, 
    # but task requires standard run. Assuming standard run is fast enough for quickstart.
    success = run_command(
        [sys.executable, "main.py"],
        "Step 2: Model Training and Evaluation"
    )
    if not success:
        logger.error("Training/Evaluation failed. Stopping quickstart.")
        finish_time = datetime.now()
        summary = {
            "status": "failed",
            "step_failed": "Training/Evaluation",
            "start_time": start_time.isoformat(),
            "end_time": finish_time.isoformat(),
            "duration_seconds": (finish_time - start_time).total_seconds()
        }
        with open(RESULTS_DIR / "quickstart_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        return 1

    # Step 3: Analysis (Interpretability & Sensitivity)
    success = run_command(
        [sys.executable, "analyze.py"],
        "Step 3: Analysis (Interpretability & Sensitivity)"
    )
    if not success:
        logger.error("Analysis failed. Stopping quickstart.")
        finish_time = datetime.now()
        summary = {
            "status": "failed",
            "step_failed": "Analysis",
            "start_time": start_time.isoformat(),
            "end_time": finish_time.isoformat(),
            "duration_seconds": (finish_time - start_time).total_seconds()
        }
        with open(RESULTS_DIR / "quickstart_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        return 1

    finish_time = datetime.now()
    duration = (finish_time - start_time).total_seconds()
    logger.info("Quickstart completed successfully!")
    logger.info(f"Total Duration: {duration:.2f} seconds")

    summary = {
        "status": "success",
        "start_time": start_time.isoformat(),
        "end_time": finish_time.isoformat(),
        "duration_seconds": duration
    }
    with open(RESULTS_DIR / "quickstart_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return 0

if __name__ == "__main__":
    sys.exit(main())
