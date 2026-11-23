import sys
import logging
import json
from pathlib import Path

# Import setup_logging from the existing config module
from src.config import setup_logging
from datasets import load_dataset

def verify_dataset_existence():
    """
    Verifies the availability of the required datasets:
    1. eBird: 'vvud/eb-data' (required)
    2. Climate: 'noaa/prism' or 'daymet/annual' (at least one required)

    Writes a JSON report to data/provenance/data_availability_report.json.
    Raises RuntimeError if the required eBird dataset is missing.
    """
    logger = setup_logging()
    logger.info("Starting dataset availability verification.")

    # Initialize flags
    ebird_available = False
    noaa_available = False
    daymet_available = False

    # 1. Verify eBird dataset (Required)
    ebird_dataset_id = "vvud/eb-data"
    try:
        logger.info(f"Attempting to verify availability of {ebird_dataset_id}...")
        # Use streaming=True to avoid downloading the full dataset just for verification
        # This checks if the dataset exists and is accessible without loading it into memory
        dataset = load_dataset(ebird_dataset_id, split="train", streaming=True)
        # Attempt to fetch the first item to confirm connectivity and validity
        next(iter(dataset))
        ebird_available = True
        logger.info(f"Success: {ebird_dataset_id} is available.")
    except Exception as e:
        logger.error(f"Failed to access {ebird_dataset_id}: {str(e)}")
        # Do not raise yet, check others first to produce a full report

    # 2. Verify NOAA/PRISM dataset (Primary Climate Source)
    noaa_dataset_id = "noaa/prism"
    try:
        logger.info(f"Checking availability of {noaa_dataset_id}...")
        # Check if the dataset exists in the registry
        from datasets import get_dataset_names
        all_datasets = get_dataset_names()
        if noaa_dataset_id in all_datasets:
            # Try a quick load/stream to ensure it's not broken
            dataset = load_dataset(noaa_dataset_id, streaming=True)
            next(iter(dataset))
            noaa_available = True
            logger.info(f"Success: {noaa_dataset_id} is available.")
        else:
            logger.warning(f"{noaa_dataset_id} not found in dataset registry.")
    except Exception as e:
        logger.warning(f"Failed to access {noaa_dataset_id}: {str(e)}")

    # 3. Verify Daymet dataset (Fallback Climate Source)
    daymet_dataset_id = "daymet/annual"
    try:
        logger.info(f"Checking availability of {daymet_dataset_id}...")
        from datasets import get_dataset_names
        all_datasets = get_dataset_names()
        if daymet_dataset_id in all_datasets:
            dataset = load_dataset(daymet_dataset_id, streaming=True)
            next(iter(dataset))
            daymet_available = True
            logger.info(f"Success: {daymet_dataset_id} is available.")
        else:
            logger.warning(f"{daymet_dataset_id} not found in dataset registry.")
    except Exception as e:
        logger.warning(f"Failed to access {daymet_dataset_id}: {str(e)}")

    # Construct report
    report = {
        "ebird_available": ebird_available,
        "noaa_available": noaa_available,
        "daymet_available": daymet_available
    }

    # Ensure output directory exists
    output_dir = Path("data/provenance")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "data_availability_report.json"

    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Availability report written to {output_path}")

    # Fail loudly if the critical eBird dataset is missing
    if not ebird_available:
        raise RuntimeError(
            f"CRITICAL FAILURE: Required dataset '{ebird_dataset_id}' is not available. "
            f"NOAA available: {noaa_available}, Daymet available: {daymet_available}. "
            f"Cannot proceed without eBird data."
        )

    logger.info("Dataset verification completed successfully.")
    return report

def main():
    """Entry point for the script."""
    verify_dataset_existence()

if __name__ == "__main__":
    main()
