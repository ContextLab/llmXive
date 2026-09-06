"""
Pipeline runner with timer wrapper.

Executes the full pipeline sequence:
1. download_data.py
2. preprocess.py
3. orchestration_check.py (T015b - inserted here to check for degenerate halt)
4. train_models.py
5. analyze_explainability.py

Records start/end timestamps and enforces the 6-hour limit.
"""
import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from utils import setup_logging

logger = setup_logging(__name__)

RESULTS_DIR = Path("results/reports")
PIPELINE_START_FILE = RESULTS_DIR / "pipeline_start.json"
PIPELINE_END_FILE = RESULTS_DIR / "pipeline_end.json"

# Define the pipeline steps
# Note: T015b (orchestration_check.py) is inserted after preprocessing
PIPELINE_SCRIPTS = [
    "code/download_data.py",
    "code/preprocess.py",
    "code/orchestration_check.py",  # T015b: Checks for degenerate flag
    "code/train_models.py",
    "code/analyze_explainability.py"
]

MAX_DURATION_HOURS = 6

def ensure_directories():
    """Ensure required output directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("models/artifacts").mkdir(parents=True, exist_ok=True)

def record_timestamp(filepath: Path, label: str):
    """Record the current timestamp to a JSON file."""
    timestamp = datetime.now().isoformat()
    data = {
        label: timestamp,
        "utc_now": datetime.utcnow().isoformat()
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Recorded {label}: {timestamp}")

def run_script(script_path: str) -> bool:
    """
    Run a specific script.
    
    Args:
        script_path: Relative path to the script.
        
    Returns:
        bool: True if successful, False if failed.
    """
    full_path = Path(script_path)
    if not full_path.exists():
        logger.error(f"Script not found: {full_path}")
        return False
    
    logger.info(f"Executing: {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, str(full_path)],
            check=True,
            capture_output=False,
            text=True
        )
        # Check exit code explicitly
        if result.returncode != 0:
            logger.error(f"Script {script_path} exited with code {result.returncode}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_path} failed with exception: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running {script_path}: {e}")
        return False

def main():
    """Main pipeline execution logic."""
    ensure_directories()
    
    # Record Start Time
    record_timestamp(PIPELINE_START_FILE, "start_time")
    start_time = datetime.now()
    
    logger.info("Starting Pipeline Execution...")
    
    for script in PIPELINE_SCRIPTS:
        logger.info(f"--- Running {script} ---")
        success = run_script(script)
        
        if not success:
            logger.error(f"Pipeline halted due to failure in {script}")
            # Record end time even on failure
            record_timestamp(PIPELINE_END_FILE, "end_time")
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Pipeline duration: {duration}")
            sys.exit(1)
        
        # Check for degenerate flag explicitly after preprocess/orth check
        # The orchestration_check.py handles the exit, but we verify here too
        if "orchestration_check.py" in script:
            # If we are here, the check passed (didn't exit), so we continue
            pass

    # Record End Time
    record_timestamp(PIPELINE_END_FILE, "end_time")
    end_time = datetime.now()
    
    duration = end_time - start_time
    duration_hours = duration.total_seconds() / 3600
    
    logger.info(f"Pipeline completed successfully in {duration} ({duration_hours:.2f} hours)")
    
    if duration_hours > MAX_DURATION_HOURS:
        logger.error(f"Pipeline exceeded {MAX_DURATION_HOURS}-hour limit.")
        sys.exit(1)
    
    logger.info("Pipeline finished within time limits.")
    sys.exit(0)

if __name__ == "__main__":
    main()