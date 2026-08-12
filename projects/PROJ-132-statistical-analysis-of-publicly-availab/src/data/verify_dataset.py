"""
Task T005a: Verify Data Availability

This script attempts to load the verified eBird sample (vvud/eb-data) and checks
for NOAA/PRISM and Daymet availability using the Hugging Face datasets library.

It writes a JSON report to data/provenance/data_availability_report.json.
If eBird is missing, it raises a RuntimeError.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Import logging setup from existing config module
from src.config import setup_logging

# Import load_dataset from the datasets library
from datasets import load_dataset, get_dataset_names

# Configure logger
logger = setup_logging("verify_dataset")


def verify_dataset_existence() -> Dict[str, bool]:
    """
    Verifies the availability of required datasets: eBird, NOAA/PRISM, and Daymet.

    Returns:
        Dict[str, bool]: Keys are dataset names, values are True if available.
    """
    results = {
        "ebird_available": False,
        "noaa_available": False,
        "daymet_available": False
    }

    # 1. Check eBird (vvud/eb-data)
    try:
        logger.info("Attempting to verify eBird dataset (vvud/eb-data)...")
        # We use streaming=True to avoid downloading the full dataset for the check
        # and to respect memory constraints. We just try to initialize the iterator.
        ds = load_dataset("vvud/eb-data", split="train", streaming=True)
        # Attempt to fetch the first item to ensure the connection and dataset exist
        next(iter(ds))
        results["ebird_available"] = True
        logger.info("eBird dataset (vvud/eb-data) is available.")
    except Exception as e:
        logger.error(f"eBird dataset (vvud/eb-data) verification failed: {e}")
        results["ebird_available"] = False


    # 2. Check NOAA/PRISM
    try:
        logger.info("Checking availability of NOAA/PRISM dataset...")
        # get_dataset_names returns a list of available datasets on the hub
        # We can check if the specific dataset ID is in the list or try to load it
        # Attempting to load with streaming is a robust way to check availability
        # without downloading full metadata if possible, but get_dataset_names is safer for a quick check
        all_datasets = get_dataset_names()
        if "noaa/prism" in all_datasets:
            results["noaa_available"] = True
            logger.info("NOAA/PRISM dataset is available.")
        else:
            logger.warning("NOAA/PRISM dataset not found in Hugging Face Hub.")
            # Fallback: try to load it directly in case get_dataset_names is incomplete
            try:
                load_dataset("noaa/prism", split="train", streaming=True)
                results["noaa_available"] = True
                logger.info("NOAA/PRISM dataset is available (confirmed via direct load).")
            except Exception:
                results["noaa_available"] = False
    except Exception as e:
        logger.error(f"Error checking NOAA/PRISM availability: {e}")
        results["noaa_available"] = False


    # 3. Check Daymet
    try:
        logger.info("Checking availability of Daymet dataset...")
        all_datasets = get_dataset_names()
        if "daymet/annual" in all_datasets:
            results["daymet_available"] = True
            logger.info("Daymet dataset is available.")
        else:
            logger.warning("Daymet dataset not found in Hugging Face Hub.")
            # Fallback: try to load it directly
            try:
                load_dataset("daymet/annual", split="train", streaming=True)
                results["daymet_available"] = True
                logger.info("Daymet dataset is available (confirmed via direct load).")
            except Exception:
                results["daymet_available"] = False
    except Exception as e:
        logger.error(f"Error checking Daymet availability: {e}")
        results["daymet_available"] = False

    return results


def main() -> None:
    """
    Main entry point for T005a.
    Verifies datasets and writes the report to data/provenance/data_availability_report.json.
    Raises RuntimeError if eBird is missing.
    """
    logger.info("Starting T005a: Verify Data Availability")

    # Ensure output directory exists
    output_dir = Path("data/provenance")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "data_availability_report.json"

    try:
        availability = verify_dataset_existence()
    except Exception as e:
        logger.critical(f"Failed to verify dataset existence: {e}")
        raise RuntimeError(f"Data verification failed: {e}") from e

    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(availability, f, indent=2)

    logger.info(f"Report written to {output_path}")

    # CRITICAL REQUIREMENT: Fail loudly if eBird is missing
    if not availability["ebird_available"]:
        error_msg = "CRITICAL: eBird dataset (vvud/eb-data) is missing. Cannot proceed."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("T005a completed successfully. eBird is available.")


if __name__ == "__main__":
    main()