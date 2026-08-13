"""
Task T005a: Verify Data Availability.

This script verifies the availability of the verified eBird sample (vvud/eb-data)
and checks for Daymet climate data availability.
It writes a JSON report to data/provenance/data_availability_report.json.
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Ensure the src directory is in the path if running as a script
if Path.cwd().name == "code":
    sys.path.insert(0, str(Path.cwd().parent))

from src.config import setup_logging
from datasets import load_dataset

# Configure logging
logger = setup_logging("verify_dataset")

REPORT_PATH = Path("data/provenance/data_availability_report.json")
EBD_DATASET_NAME = "vvud/eb-data"
DAYMET_DATASET_NAME = "daymet/annual"

def verify_dataset_existence():
    """
    Verifies the availability of eBird and Daymet datasets.
    Writes a report to data/provenance/data_availability_report.json.
    Raises RuntimeError if eBird is missing.
    """
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ebird_available": False,
        "daymet_available": False,
        "ebird_error": None,
        "daymet_error": None
    }

    # Verify eBird sample
    logger.info(f"Checking availability of eBird dataset: {EBD_DATASET_NAME}")
    try:
        # Attempt to stream the dataset to verify existence without loading fully
        ds = load_dataset(EBD_DATASET_NAME, split="train", streaming=True)
        # Try to fetch one record to ensure it's not empty/corrupt
        next(iter(ds))
        report["ebird_available"] = True
        logger.info("eBird dataset is available and accessible.")
    except Exception as e:
        report["ebird_error"] = str(e)
        logger.error(f"eBird dataset check failed: {e}")
        # CRITICAL: Fail loudly if eBird is missing
        raise RuntimeError(f"eBird dataset '{EBD_DATASET_NAME}' is not available. Pipeline cannot proceed. Error: {e}")

    # Verify Daymet availability
    logger.info(f"Checking availability of Daymet dataset: {DAYMET_DATASET_NAME}")
    try:
        # Check if the dataset exists by trying to get its info or streaming
        # We use streaming=True to avoid downloading the whole dataset for a check
        ds = load_dataset(DAYMET_DATASET_NAME, streaming=True)
        # Verify we can iterate (at least one sample)
        next(iter(ds))
        report["daymet_available"] = True
        logger.info("Daymet dataset is available and accessible.")
    except Exception as e:
        report["daymet_error"] = str(e)
        logger.warning(f"Daymet dataset check failed (non-fatal for this step, but noted): {e}")
        # We log the error but do not raise RuntimeError here as per task description
        # which says "checks for Daymet availability" and only requires RuntimeError for eBird.
        # However, if the task implies Daymet is also critical for the full pipeline,
        # the downstream tasks will fail. For this specific task, we record the status.

    # Ensure output directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Data availability report written to {REPORT_PATH}")

    return report

def main():
    """Main entry point for the verification script."""
    try:
        verify_dataset_existence()
        logger.info("Verification completed successfully.")
    except RuntimeError as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
