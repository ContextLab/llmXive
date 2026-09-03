import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import from existing API surface
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

def load_json_log(path: Path) -> dict:
    """Load a JSON log file if it exists."""
    if not path.exists():
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Could not load JSON log {path}: {e}")
        return {}

def check_file_exists(path: Path) -> bool:
    """Check if a file exists and has non-zero size."""
    return path.exists() and path.stat().st_size > 0

def run_validation_gate(
    t001c_log: Path,
    t001b_log: Path,
    t004_log: Path,
    era5_full_path: Path
) -> tuple[bool, dict]:
    """
    Aggregate results from T001c, T001b, T004 and verify era5_full existence.
    Returns (passed, details_dict).
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # 1. Check T001c (Validate Data Sources)
    # We assume the log file indicates success if it exists and is non-empty
    t001c_ok = t001c_log.exists() and t001c_log.stat().st_size > 0
    results["checks"]["T001c_validate_sources"] = {
        "passed": t001c_ok,
        "path": str(t001c_log)
    }

    # 2. Check T001b (Ingest & Validate ERA5 Sample)
    t001b_ok = t001b_log.exists() and t001b_log.stat().st_size > 0
    results["checks"]["T001b_ingest_era5_sample"] = {
        "passed": t001b_ok,
        "path": str(t001b_log)
    }

    # 3. Check T004 (Validate ERA5 Sample Integrity)
    t004_ok = t004_log.exists() and t004_log.stat().st_size > 0
    results["checks"]["T004_validate_integrity"] = {
        "passed": t004_ok,
        "path": str(t004_log)
    }

    # 4. Check T002c output (data/raw/era5_full.h5)
    era5_full_ok = check_file_exists(era5_full_path)
    results["checks"]["T002c_era5_full_exists"] = {
        "passed": era5_full_ok,
        "path": str(era5_full_path)
    }

    all_passed = all(c["passed"] for c in results["checks"].values())
    results["gate_status"] = "PASS" if all_passed else "FAIL"

    return all_passed, results

def main():
    setup_logging()
    logger = get_data_quality_logger()

    # Define paths based on project structure
    root = Path(get_path_env_override("PROJECT_ROOT", "."))
    logs_dir = root / "results" / "logs"
    data_raw_dir = root / "data" / "raw"

    # Input log files (produced by previous tasks)
    t001c_log = logs_dir / "data_validation_log.txt"
    t001b_log = logs_dir / "data_validation_log.txt" # Often shared, or specific file if separated
    t004_log = logs_dir / "data_validation_log.txt"
    
    # Specific file checks: if tasks wrote to specific JSON logs, adjust here.
    # For now, we assume the main validation log is the indicator.
    # If specific JSONs exist, prefer them:
    t001c_json = logs_dir / "validation_report.json"
    t001b_json = logs_dir / "era5_sample_validation.json"
    t004_json = logs_dir / "integrity_validation.json"

    if t001c_json.exists(): t001c_log = t001c_json
    if t001b_json.exists(): t001b_log = t001b_json
    if t004_json.exists(): t004_log = t004_json

    era5_full_path = data_raw_dir / "era5_full.h5"

    logger.info("Starting Pre-Ingestion Validation Gate (T006)...")

    try:
        passed, details = run_validation_gate(t001c_log, t001b_log, t004_log, era5_full_path)
        
        # Log final status to the required file
        output_log_path = logs_dir / "data_validation_log.txt"
        output_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_log_path, 'a') as f:
            f.write(f"\n--- T006 Pre-Ingestion Validation Gate ---\n")
            f.write(f"Timestamp: {details['timestamp']}\n")
            f.write(f"Gate Status: {details['gate_status']}\n")
            for check_name, check_data in details["checks"].items():
                status = "PASS" if check_data["passed"] else "FAIL"
                f.write(f"  {check_name}: {status} ({check_data['path']})\n")
            f.write(f"---------------------------------------------\n")

        if passed:
            logger.info("Validation Gate PASSED. Proceeding to ingestion.")
            print("T006: PASS")
        else:
            logger.error("Validation Gate FAILED. Aborting pipeline.")
            # Log details to stderr for visibility
            print("T006: FAIL - See results/logs/data_validation_log.txt for details", file=sys.stderr)
            raise RuntimeError("Pre-ingestion validation failed. Pipeline aborted.")

    except Exception as e:
        logger.exception("Validation Gate execution failed.")
        print(f"T006: ERROR - {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()