import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from verify_cds_api import verify_cds_api_access
from fetch_era5 import fetch_era5_sample
from compute_checksum import compute_sha256
from validate_era5_sample import validate_era5_sample
from verify_moral_machine_source import verify_source_access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LOG_FILE = project_root / "results" / "logs" / "data_validation_log.txt"
SAMPLE_FILE = project_root / "data" / "raw" / "era5_sample.h5"
STATE_FILE = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

def ensure_directories():
    """Ensure the log directory exists."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def append_log(message: str):
    """Append a message to the log file with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    logger.info(log_entry.strip())

def main():
    ensure_directories()
    append_log("=" * 60)
    append_log("Starting Data Validation Aggregation (Task T006)")
    append_log("=" * 60)

    results = []

    # 1. Verify CDS API Access (T001)
    try:
        append_log("Executing T001: Verifying CDS API access...")
        # Re-run the verification to ensure fresh state or read existing log if preferred.
        # For robustness, we re-run the check.
        status = verify_cds_api_access()
        if status:
            append_log("T001 PASSED: CDS API is accessible.")
            results.append(("T001", "PASSED", "CDS API Access"))
        else:
            append_log("T001 FAILED: CDS API access verification failed.")
            results.append(("T001", "FAILED", "CDS API Access"))
    except Exception as e:
        append_log(f"T001 ERROR: {str(e)}")
        results.append(("T001", "ERROR", f"CDS API Access: {e}"))

    # 2. Fetch ERA5 Sample (T002) - Assuming file exists from previous run, but we check
    try:
        append_log("Executing T002: Checking ERA5 sample file...")
        if SAMPLE_FILE.exists():
            append_log(f"T002 PASSED: Sample file exists at {SAMPLE_FILE}")
            results.append(("T002", "PASSED", "ERA5 Sample Download"))
        else:
            # Attempt to fetch if missing (optional, but task says T002 is done)
            # If T002 is marked complete, we assume the file should exist.
            # If not, we flag it.
            append_log("T002 FAILED: Sample file not found. T002 may not have completed successfully.")
            results.append(("T002", "FAILED", "ERA5 Sample Download - File Missing"))
    except Exception as e:
        append_log(f"T002 ERROR: {str(e)}")
        results.append(("T002", "ERROR", f"ERA5 Sample Download: {e}"))

    # 3. Compute Checksum (T003)
    try:
        append_log("Executing T003: Computing SHA-256 checksum...")
        if SAMPLE_FILE.exists():
            checksum = compute_sha256(SAMPLE_FILE)
            append_log(f"T003 PASSED: Checksum computed: {checksum}")
            results.append(("T003", "PASSED", f"Checksum: {checksum}"))
        else:
            append_log("T003 FAILED: Cannot compute checksum, sample file missing.")
            results.append(("T003", "FAILED", "Checksum - File Missing"))
    except Exception as e:
        append_log(f"T003 ERROR: {str(e)}")
        results.append(("T003", "ERROR", f"Checksum: {e}"))

    # 4. Validate ERA5 Sample (T004)
    try:
        append_log("Executing T004: Validating ERA5 sample resolution...")
        if SAMPLE_FILE.exists():
            is_valid = validate_era5_sample(SAMPLE_FILE)
            if is_valid:
                append_log("T004 PASSED: ERA5 sample meets resolution standards.")
                results.append(("T004", "PASSED", "ERA5 Resolution Validation"))
            else:
                append_log("T004 FAILED: ERA5 sample does not meet resolution standards.")
                results.append(("T004", "FAILED", "ERA5 Resolution Validation"))
        else:
            append_log("T004 FAILED: Cannot validate, sample file missing.")
            results.append(("T004", "FAILED", "ERA5 Resolution - File Missing"))
    except Exception as e:
        append_log(f"T004 ERROR: {str(e)}")
        results.append(("T004", "ERROR", f"ERA5 Resolution: {e}"))

    # 5. Verify Moral Machine Source (T005)
    try:
        append_log("Executing T005: Verifying Moral Machine source...")
        status = verify_source_access()
        if status:
            append_log("T005 PASSED: Moral Machine source is accessible and valid.")
            results.append(("T005", "PASSED", "Moral Machine Source"))
        else:
            append_log("T005 FAILED: Moral Machine source verification failed.")
            results.append(("T005", "FAILED", "Moral Machine Source"))
    except Exception as e:
        append_log(f"T005 ERROR: {str(e)}")
        results.append(("T005", "ERROR", f"Moral Machine Source: {e}"))

    # Aggregate Results
    append_log("=" * 60)
    append_log("FINAL VALIDATION SUMMARY")
    append_log("=" * 60)

    passed_count = sum(1 for r in results if r[1] == "PASSED")
    failed_count = sum(1 for r in results if r[1] == "FAILED")
    error_count = sum(1 for r in results if r[1] == "ERROR")

    for task_id, status, detail in results:
        append_log(f"{task_id}: {status} - {detail}")

    append_log("-" * 60)
    if failed_count == 0 and error_count == 0:
        append_log("OVERALL STATUS: PASSED")
        append_log("Data validation complete. All checks passed. Proceed to Phase 1.")
    else:
        append_log("OVERALL STATUS: FAILED")
        append_log(f"Validation failed. {failed_count} failures, {error_count} errors.")
        append_log("Project is BLOCKED until data issues are resolved.")

    append_log("=" * 60)
    append_log("End of Validation Report")
    append_log("=" * 60)

    return 0 if failed_count == 0 and error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())