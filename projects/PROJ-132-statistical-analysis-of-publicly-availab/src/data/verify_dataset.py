import sys
import logging
import json
from pathlib import Path

from datasets import load_dataset
from src.config import setup_logging

logger = logging.getLogger(__name__)

def verify_dataset_existence(dataset_name: str = "vvud/eb-data") -> bool:
    """
    Verify the existence of the specified dataset on HuggingFace.

    Args:
        dataset_name: The HuggingFace dataset identifier.

    Returns:
        True if the dataset exists and is accessible.

    Raises:
        RuntimeError: If the dataset is not found or accessible.
    """
    logger.info(f"Verifying existence of dataset: {dataset_name}")
    try:
        # Attempt to load the dataset info to verify existence without downloading full data
        # Using streaming=False but split="train" to trigger existence check quickly
        # trust_remote_code is required per task spec for this specific dataset
        ds = load_dataset(dataset_name, split="train", trust_remote_code=True)
        logger.info(f"Dataset '{dataset_name}' verified successfully. Rows: {len(ds)}")
        return True
    except Exception as e:
        error_msg = f"Dataset '{dataset_name}' not found or inaccessible: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def main():
    """
    Main entry point for verifying the eBird sample dataset.
    Writes a JSON report to data/provenance/data_availability_report.json.
    """
    # Setup logging
    setup_logging()

    output_dir = Path("data/provenance")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "data_availability_report.json"

    dataset_name = "vvud/eb-data"
    climate_dataset_name = "daymet/annual"

    report = {
        "full_ebd_available": False,
        "sample_scope_adopted": False,
        "climate_data_available": False,
        "source": "unknown"
    }

    try:
        # Verify eBird sample dataset
        if verify_dataset_existence(dataset_name):
            report["sample_scope_adopted"] = True
            report["source"] = dataset_name
            logger.info(f"Verified sample dataset: {dataset_name}")
        else:
            raise RuntimeError(f"Sample dataset {dataset_name} verification failed.")

        # Verify climate dataset
        try:
            if verify_dataset_existence(climate_dataset_name):
                report["climate_data_available"] = True
                logger.info(f"Verified climate dataset: {climate_dataset_name}")
        except RuntimeError as e:
            logger.warning(f"Climate dataset check failed: {e}")
            report["climate_data_available"] = False

        # Write report
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Data availability report written to {output_file}")
        print(f"Success: {output_file}")

    except RuntimeError as e:
        logger.error(f"Verification failed: {e}")
        # Even on failure, write a partial report if possible, or fail loudly
        report["source"] = "error"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        raise

if __name__ == "__main__":
    main()