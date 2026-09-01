"""
Task T005a: Log Data Availability Status.

Logic:
1. Check if `data/raw/agenticsts_trajectories.jsonl` exists.
2. If missing:
   - Write an ERROR log to `data/processed/edge_case_warnings.log`.
   - Set `PIPELINE_BLOCKED=true` in `data/processed/config_state.json`.
   - Raise a RuntimeError to halt the pipeline (fail loudly).
3. If present:
   - Write an INFO log confirming data availability.
   - Ensure `PIPELINE_BLOCKED=false` in `data/processed/config_state.json`.

Constraint: This task runs AFTER T005b.
"""

import os
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TARGET_FILE = DATA_RAW_DIR / "agenticsts_trajectories.jsonl"
WARNING_LOG_FILE = DATA_PROCESSED_DIR / "edge_case_warnings.log"
CONFIG_STATE_FILE = DATA_PROCESSED_DIR / "config_state.json"

def ensure_directories():
    """Ensure required output directories exist."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def write_warning_log(message: str, level: str = "ERROR"):
    """Append a timestamped log entry to the edge case warnings log."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = json.dumps({
        "level": level,
        "message": message,
        "timestamp": timestamp
    })
    with open(WARNING_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    logger.log(
        logging.ERROR if level == "ERROR" else logging.INFO,
        f"Logged to {WARNING_LOG_FILE}: {log_entry}"
    )

def update_config_state(blocked: bool):
    """Update the pipeline configuration state file."""
    state = {
        "pipeline_blocked": blocked,
        "last_check": datetime.utcnow().isoformat() + "Z",
        "data_source": "agenticsts_trajectories.jsonl"
    }
    with open(CONFIG_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    logger.info(f"Updated config state: PIPELINE_BLOCKED={blocked}")

def main():
    """
    Main entry point for Task T005a.
    Checks for the existence of the real data file and updates pipeline state.
    """
    ensure_directories()

    if not TARGET_FILE.exists():
        logger.error(f"Real data missing: {TARGET_FILE}")
        msg = "Real data missing; pipeline blocked."
        
        # Log the error to the warnings file
        write_warning_log(msg, level="ERROR")
        
        # Update config state to block the pipeline
        update_config_state(blocked=True)
        
        # FAIL LOUDLY: The pipeline must stop if real data is missing.
        # Do not fall back to synthetic data.
        raise FileNotFoundError(msg)
    
    else:
        logger.info(f"Real data found: {TARGET_FILE}")
        msg = "Real data available; pipeline proceeding."
        
        # Log success
        write_warning_log(msg, level="INFO")
        
        # Update config state to allow pipeline
        update_config_state(blocked=False)
        
        logger.info("T005a completed successfully.")

if __name__ == "__main__":
    main()
