"""
T005a: Generate No-Data Warning

This task generates a warning log if no trajectory data is available.
It runs AFTER T005b and T006a to detect if T006a was skipped due to missing input.

NOTE: This task must NOT generate synthetic data. It only logs a warning.
"""
import os
import logging
from pathlib import Path
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_PROCESSED_DIR = Path("data/processed")
WARNING_LOG_FILE = DATA_PROCESSED_DIR / "edge_case_warnings.log"

def main() -> None:
    """Main entry point for T005a."""
    logger.info("Starting T005a: Generating No-Data Warning")
    
    # Check if this should run (CI=false or local dev where CI is not running)
    ci_mode = os.environ.get("CI", "false").lower() == "true"
    
    if ci_mode:
        logger.info("CI mode detected. Skipping warning generation.")
        return
    
    # Check if input data exists
    raw_data_dir = Path("data/raw")
    if raw_data_dir.exists() and list(raw_data_dir.glob("*.jsonl")):
        logger.info("Input data found. No warning needed.")
        return
    
    # Generate warning
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    warning_entry = {
        "level": "WARN",
        "message": "No trajectory data available for entropy calculation; pipeline cannot proceed.",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(WARNING_LOG_FILE, "a") as f:
        f.write(json.dumps(warning_entry) + "\n")
    
    logger.warning(f"Warning written to {WARNING_LOG_FILE}")

if __name__ == "__main__":
    main()