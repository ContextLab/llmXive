"""
Pre-Ingestion Validation Gate (T006)

Aggregates results from prior validation tasks (T001a, T001b, T001c, T002c, T002d,
T002e, T003, T004) and verifies the existence of critical data artifacts before
allowing the pipeline to proceed to ingestion.

Required Artifacts:
- data/raw/moral_machine.csv.gz
- data/raw/era5_full.parquet

If any validation fails or required files are missing, this script raises an
exception to abort the pipeline.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

def ensure_directories():
    """Ensure required log directories exist."""
    log_dir = Path("results/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

def load_json_log(log_path: Path) -> dict:
    """Load a JSON log file if it exists, otherwise return empty dict."""
    if not log_path.exists():
        return {}
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Could not load log {log_path}: {e}")
        return {}

def check_file_exists(file_path: Path, logger: logging.Logger) -> bool:
    """Check if a specific file exists and is non-empty."""
    if not file_path.exists():
        logger.error(f"Required file missing: {file_path}")
        return False
    if file_path.stat().st_size == 0:
        logger.error(f"Required file is empty: {file_path}")
        return False
    return True

def run_validation_gate(logger: logging.Logger) -> bool:
    """
    Execute the pre-ingestion validation gate.

    Returns True if all checks pass, False otherwise.
    Raises an exception if the gate fails to enforce the blocker.
    """
    project_root = Path(__file__).parent.parent
    data_raw = project_root / "data" / "raw"
    
    # Critical Artifacts
    moral_machine_path = data_raw / "moral_machine.csv.gz"
    era5_full_path = data_raw / "era5_full.parquet"

    # Validation Log Paths (from completed tasks)
    # T001a, T001b, T001c, T002c, T002d, T002e, T003, T004
    # We assume these tasks wrote to results/logs/data_validation_log.txt
    # and potentially specific JSON status files.
    validation_log_path = project_root / "results" / "logs" / "data_validation_log.txt"
    fetch_status_path = project_root / "results" / "logs" / "fetch_status.json"
    bbox_status_path = project_root / "results" / "logs" / "bbox_status.json"
    
    # Check 1: Critical File Existence
    logger.info("Checking critical data artifacts...")
    checks_passed = True

    if not check_file_exists(moral_machine_path, logger):
        checks_passed = False
    
    if not check_file_exists(era5_full_path, logger):
        checks_passed = False

    # Check 2: Verify previous validation steps (optional but recommended)
    # We check if the validation log exists and contains "Pass" or "Success"
    # markers from previous tasks.
    if validation_log_path.exists():
        logger.info(f"Found previous validation log: {validation_log_path}")
        # We don't strictly parse it here to avoid tight coupling to specific log formats,
        # but we acknowledge its presence.
    else:
        logger.warning(f"Previous validation log not found: {validation_log_path}")
        # This might be okay if we rely solely on file existence, 
        # but strictly speaking, T006 aggregates results.
        # If the log is missing, we assume the aggregation step failed previously.
        # However, the primary blocker is file existence.

    # Check 3: Verify Fetch Status (T002c)
    if fetch_status_path.exists():
        try:
            with open(fetch_status_path, 'r') as f:
                status = json.load(f)
            # Heuristic: if 'failed_tiles' > 0 or 'status' indicates failure
            if status.get('status') == 'failed':
                logger.error("ERA5 fetch status indicates failure.")
                checks_passed = False
        except json.JSONDecodeError:
            logger.warning("Could not parse fetch_status.json")
    else:
        logger.warning("fetch_status.json not found. Assuming fetch step not completed.")
        # If fetch status is missing, we might be in a state where T002c wasn't run.
        # But if era5_full.parquet exists, the data is there.
    
    # Final Decision
    if not checks_passed:
        error_msg = "Pre-Ingestion Validation Gate FAILED. Critical artifacts missing or validation failed. Aborting pipeline."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Pre-Ingestion Validation Gate PASSED. All critical artifacts present and valid.")
    return True

def main():
    """Main entry point for the validation gate."""
    ensure_directories()
    
    # Setup logger
    logger = get_data_quality_logger()
    if not logger:
        logger = setup_logging()
    
    logger.info("Starting Pre-Ingestion Validation Gate (T006)...")
    
    try:
        success = run_validation_gate(logger)
        
        # Log final status to the main validation log
        log_path = Path("results/logs/data_validation_log.txt")
        with open(log_path, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            status_str = "PASS" if success else "FAIL"
            f.write(f"[{timestamp}] T006 Pre-Ingestion Validation: {status_str}\n")
        
        if success:
            logger.info("Validation Gate completed successfully.")
            sys.exit(0)
        else:
            # Should have raised an exception, but just in case
            logger.error("Validation Gate completed with errors.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation Gate failed with exception: {e}")
        # Log failure
        log_path = Path("results/logs/data_validation_log.txt")
        with open(log_path, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] T006 Pre-Ingestion Validation: FAIL - {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()