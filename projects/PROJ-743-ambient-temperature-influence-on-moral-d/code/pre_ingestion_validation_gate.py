"""
Pre-Ingestion Validation Gate (T006)

Aggregates results from T001-T005.
Reads JSON log files from T001a, T001c, T004, T005 and checks file existence for T002c.
If ANY source validation (ERA5 or Moral Machine) fails, raises an exception and aborts.
Logs the final gate status (Pass/Fail) to results/logs/data_validation_log.txt.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import logging setup from existing module to ensure consistency
from setup_logging import setup_logging, get_data_quality_logger

def load_json_log(file_path: Path) -> dict:
    """Load a JSON log file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required log file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.exists()

def run_validation_gate():
    """
    Execute the pre-ingestion validation gate.
    Returns True if all checks pass, False otherwise.
    """
    # Setup logging
    logger = setup_logging()
    data_logger = get_data_quality_logger()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    results_dir = project_root / "results"
    logs_dir = results_dir / "logs"

    # Ensure log directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Define paths to validation artifacts based on T001-T005
    # T001a: Moral Machine Source Validation
    moral_machine_log_path = logs_dir / "moral_machine_validation.json"
    
    # T001c: ERA5 Citation Validation
    era5_metadata_log_path = logs_dir / "era5_metadata_validation.json"
    
    # T004: ERA5 Sample Resolution Validation
    era5_sample_validation_log_path = logs_dir / "era5_sample_resolution_validation.json"
    
    # T005: Moral Machine Source Verification (Duplicate/Redundant check, but per spec)
    moral_machine_verify_log_path = logs_dir / "moral_machine_source_verify.json"
    
    # T002c: Full ERA5 Fetch Output File
    era5_full_file_path = data_dir / "raw" / "era5_full.h5"

    # Initialize status
    gate_status = "PASS"
    errors = []

    logger.info("=" * 60)
    logger.info("Starting Pre-Ingestion Validation Gate (T006)")
    logger.info("=" * 60)

    # 1. Check T001a: Moral Machine Source Validation
    logger.info("Checking T001a: Moral Machine Source Validation...")
    try:
        mm_log = load_json_log(moral_machine_log_path)
        if mm_log.get("status") != "Pass":
            errors.append(f"T001a Failed: {mm_log.get('reason', 'Unknown reason')}")
            gate_status = "FAIL"
        else:
            logger.info("T001a: PASS")
    except FileNotFoundError as e:
        errors.append(f"T001a: Missing log file - {e}")
        gate_status = "FAIL"
    except json.JSONDecodeError as e:
        errors.append(f"T001a: Invalid JSON in log file - {e}")
        gate_status = "FAIL"

    # 2. Check T001c: ERA5 Citation Validation
    logger.info("Checking T001c: ERA5 Citation Validation...")
    try:
        era5_meta_log = load_json_log(era5_metadata_log_path)
        if era5_meta_log.get("status") != "Pass":
            errors.append(f"T001c Failed: {era5_meta_log.get('reason', 'Unknown reason')}")
            gate_status = "FAIL"
        else:
            logger.info("T001c: PASS")
    except FileNotFoundError as e:
        errors.append(f"T001c: Missing log file - {e}")
        gate_status = "FAIL"
    except json.JSONDecodeError as e:
        errors.append(f"T001c: Invalid JSON in log file - {e}")
        gate_status = "FAIL"

    # 3. Check T004: ERA5 Sample Resolution Validation
    logger.info("Checking T004: ERA5 Sample Resolution Validation...")
    try:
        era5_sample_log = load_json_log(era5_sample_validation_log_path)
        if era5_sample_log.get("status") != "Pass":
            errors.append(f"T004 Failed: {era5_sample_log.get('reason', 'Unknown reason')}")
            gate_status = "FAIL"
        else:
            logger.info("T004: PASS")
    except FileNotFoundError as e:
        errors.append(f"T004: Missing log file - {e}")
        gate_status = "FAIL"
    except json.JSONDecodeError as e:
        errors.append(f"T004: Invalid JSON in log file - {e}")
        gate_status = "FAIL"

    # 4. Check T005: Moral Machine Source Verification
    logger.info("Checking T005: Moral Machine Source Verification...")
    try:
        mm_verify_log = load_json_log(moral_machine_verify_log_path)
        if mm_verify_log.get("status") != "Pass":
            errors.append(f"T005 Failed: {mm_verify_log.get('reason', 'Unknown reason')}")
            gate_status = "FAIL"
        else:
            logger.info("T005: PASS")
    except FileNotFoundError as e:
        errors.append(f"T005: Missing log file - {e}")
        gate_status = "FAIL"
    except json.JSONDecodeError as e:
        errors.append(f"T005: Invalid JSON in log file - {e}")
        gate_status = "FAIL"

    # 5. Check T002c: Full ERA5 Fetch Output File Existence
    logger.info("Checking T002c: Full ERA5 Fetch Output File Existence...")
    if not check_file_exists(era5_full_file_path):
        errors.append(f"T002c Failed: Expected file not found - {era5_full_file_path}")
        gate_status = "FAIL"
    else:
        logger.info("T002c: PASS (File exists)")

    # Log Final Results
    timestamp = datetime.now().isoformat()
    final_log_entry = {
        "task_id": "T006",
        "timestamp": timestamp,
        "gate_status": gate_status,
        "errors": errors
    }

    log_file_path = logs_dir / "data_validation_log.txt"
    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(f"\n--- T006 Pre-Ingestion Validation Gate ---\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Status: {gate_status}\n")
        if errors:
            f.write("Errors:\n")
            for err in errors:
                f.write(f"  - {err}\n")
        f.write(f"-------------------------------------------\n")

    if gate_status == "FAIL":
        logger.error("VALIDATION GATE FAILED. Aborting pipeline.")
        for err in errors:
            logger.error(f"  {err}")
        raise RuntimeError(f"Pre-Ingestion Validation Gate Failed: {errors}")
    
    logger.info("VALIDATION GATE PASSED. Proceeding to ingestion.")
    return True

def main():
    try:
        run_validation_gate()
        print("Pre-Ingestion Validation Gate (T006): PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"Pre-Ingestion Validation Gate (T006): FAILED - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
