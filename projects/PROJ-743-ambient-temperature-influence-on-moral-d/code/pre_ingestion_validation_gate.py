"""
Pre-Ingestion Validation Gate (T006)

Aggregates results from prior validation tasks (T001a, T001b, T001c, T001d, T004)
and verifies the existence of the full ERA5 dataset (T002d).
If any validation fails or required files are missing, raises an exception to abort the pipeline.
Logs the final gate status to results/logs/data_validation_log.txt.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import shared utilities from existing API surface
from setup_logging import get_data_quality_logger, ensure_directories
from config import get_path_env_override

# Define expected file paths based on task descriptions
# T001a, T001b, T001c, T001d, T004 all log to this file
VALIDATION_LOG_PATH = Path("results/logs/data_validation_log.txt")

# T002d output
ERA5_FULL_PARQUET_PATH = Path("data/raw/era5_full.parquet")

# Checksum state file (T002e, T003)
STATE_FILE_PATH = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")

def load_json_log(log_path: Path) -> dict:
    """
    Attempt to load a JSON log file if it exists.
    Returns an empty dict if the file is missing or invalid JSON.
    """
    if not log_path.exists():
        return {}
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a required file exists. Log result and return status."""
    if path.exists():
        logging.info(f"[VALIDATION] {description} exists: {path}")
        return True
    else:
        logging.error(f"[VALIDATION] {description} MISSING: {path}")
        return False

def run_validation_gate(logger: logging.Logger) -> bool:
    """
    Execute the pre-ingestion validation gate logic.
    Returns True if all checks pass, False otherwise.
    """
    all_checks_passed = True
    timestamp = datetime.now().isoformat()
    
    logger.info(f"Starting Pre-Ingestion Validation Gate at {timestamp}")
    logger.info("Dependencies: T001a, T001b, T001c, T001d, T004, T002c, T002d, T002e")

    # 1. Verify ERA5 Full Dataset Existence (T002d)
    logger.info("Checking for data/raw/era5_full.parquet (T002d output)...")
    if not check_file_exists(ERA5_FULL_PARQUET_PATH, "Full ERA5 Dataset"):
        all_checks_passed = False
    
    # 2. Verify Validation Log Existence (T001a, T001b, T001c, T001d, T004)
    # We assume the log exists if previous tasks ran, but we check its content for "Fail" markers
    logger.info("Checking validation log for prior failures...")
    if VALIDATION_LOG_PATH.exists():
        try:
            with open(VALIDATION_LOG_PATH, 'r', encoding='utf-8') as f:
                log_content = f.read()
                if "FAIL" in log_content.upper() or "ERROR" in log_content.upper():
                    logger.error("[VALIDATION] Prior validation logs contain failure indicators.")
                    all_checks_passed = False
                else:
                    logger.info("[VALIDATION] Prior validation logs appear clean.")
        except Exception as e:
            logger.error(f"[VALIDATION] Could not read validation log: {e}")
            all_checks_passed = False
    else:
        logger.warning("[VALIDATION] Validation log file not found. Assuming prior tasks did not run or failed.")
        # This might be acceptable if T001 tasks haven't run, but T006 depends on them.
        # Strictly speaking, if T001 tasks are marked done, this file should exist.
        # We will treat missing log as a failure if we expect it.
        all_checks_passed = False

    # 3. Verify State File Integrity (T002e, T003)
    logger.info("Checking state file for checksum records...")
    if not check_file_exists(STATE_FILE_PATH, "Project State File"):
        all_checks_passed = False
    else:
        # Optional: Verify specific keys exist in state file if needed
        try:
            import yaml
            with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
                state = yaml.safe_load(f)
                if not state or 'artifact_hashes' not in state:
                    logger.warning("[VALIDATION] State file exists but lacks 'artifact_hashes' section.")
                    # Not a hard fail if we just check existence, but good to note
        except Exception as e:
            logger.error(f"[VALIDATION] Could not parse state file: {e}")
            all_checks_passed = False

    # Final Decision
    if all_checks_passed:
        logger.info("Pre-Ingestion Validation Gate: PASSED")
        return True
    else:
        logger.error("Pre-Ingestion Validation Gate: FAILED - Aborting pipeline.")
        return False

def main():
    """Main entry point for the validation gate."""
    # Ensure output directories exist
    ensure_directories()
    
    # Setup logging
    logger = get_data_quality_logger()
    
    try:
        success = run_validation_gate(logger)
        
        # Append final status to the validation log file
        with open(VALIDATION_LOG_PATH, 'a', encoding='utf-8') as f:
            status = "PASSED" if success else "FAILED"
            f.write(f"{datetime.now().isoformat()} - Pre-Ingestion Gate: {status}\n")
        
        if not success:
            # Fail loudly as per constraints
            raise RuntimeError("Pre-Ingestion Validation Gate Failed. Pipeline aborted.")
            
        print("Validation Gate Successful.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation Gate Exception: {e}")
        # Ensure failure is logged
        with open(VALIDATION_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - Pre-Ingestion Gate: FAILED - Exception: {e}\n")
        raise

if __name__ == "__main__":
    main()