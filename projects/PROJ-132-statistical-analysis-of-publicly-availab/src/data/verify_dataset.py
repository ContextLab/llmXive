"""
Task T005a: Verify Data Availability.

This script attempts to load the verified eBird sample (vvud/eb-data) using
streaming and checks for Daymet availability. It writes a report to
data/provenance/data_availability_report.json.

It raises RuntimeError if the eBird dataset is missing.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure src is in path for imports if running as script
if __name__ == "__main__":
    src_root = Path(__file__).resolve().parent.parent
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from datasets import load_dataset
from src.config import setup_logging

LOGGER = setup_logging("verify_dataset")

def verify_dataset_existence():
    """
    Verifies availability of eBird (vvud/eb-data) and Daymet datasets.
    Writes results to data/provenance/data_availability_report.json.
    Raises RuntimeError if eBird is missing.
    """
    report_path = Path("data/provenance/data_availability_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    ebird_available = False
    daymet_available = False

    # 1. Verify eBird (vvud/eb-data)
    LOGGER.info("Checking availability of eBird dataset (vvud/eb-data)...")
    try:
        # Use streaming=True as per task requirement to avoid loading full dataset into memory
        dataset = load_dataset("vvud/eb-data", split="train", streaming=True)
        # Attempt to fetch one record to confirm connectivity and validity
        first_record = next(iter(dataset))
        if first_record:
            ebird_available = True
            LOGGER.info("eBird dataset (vvud/eb-data) is available and accessible.")
        else:
            LOGGER.warning("eBird dataset returned empty stream.")
    except Exception as e:
        LOGGER.error(f"Failed to load eBird dataset: {e}")
        ebird_available = False

    # 2. Verify Daymet availability
    # Note: Daymet is often accessed via specific IDs or URLs.
    # We attempt to load a known Daymet annual dataset if available via HuggingFace.
    LOGGER.info("Checking availability of Daymet dataset...")
    try:
        # Attempting to load a common Daymet annual dataset on HuggingFace
        # If this specific ID is not found, we catch the exception.
        # Common IDs: "daymet/annual", "daymet/short"
        daymet_ds = load_dataset("daymet/annual", streaming=True)
        # Verify stream is not empty
        next(iter(daymet_ds))
        daymet_available = True
        LOGGER.info("Daymet dataset is available.")
    except Exception as e:
        # Daymet might not be on HF directly or requires specific config
        # We log the error but do not fail the whole script unless eBird is missing
        LOGGER.warning(f"Daymet dataset not found or inaccessible via 'daymet/annual': {e}")
        daymet_available = False

    # 3. Generate Report
    report = {
        "ebird_available": ebird_available,
        "daymet_available": daymet_available,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    LOGGER.info(f"Availability report written to {report_path}")

    # CRITICAL: Fail loudly if eBird is missing
    if not ebird_available:
        raise RuntimeError("eBird dataset (vvud/eb-data) is missing or inaccessible. Aborting pipeline.")

    return report

def main():
    """Entry point for the verification script."""
    try:
        result = verify_dataset_existence()
        print(f"Verification successful. Report: {result}")
        return 0
    except RuntimeError as e:
        print(f"Verification failed: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
