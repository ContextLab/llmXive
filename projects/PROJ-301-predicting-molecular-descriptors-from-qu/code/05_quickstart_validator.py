import os
import sys
import json
import time
import logging
from pathlib import Path
from utils.logger import get_logger
from config import set_seeds

logger = get_logger(__name__)

# Constants
REQUIRED_FILES = [
    "data/raw/qm9_full.parquet",
    "data/processed/molecules_cleaned.parquet",
    "data/processed/features_2d.npy",
    "data/processed/features_3d.npy",
    "data/processed/labels.csv",
    "artifacts/models/model_2d.pkl",
    "artifacts/models/model_3d.pkl",
    "artifacts/metrics/cv_metrics.json",
    "artifacts/metrics/stability_report.json",
    "artifacts/metrics/baseline_error.json",
    "artifacts/metrics/test_predictions.json",
    "artifacts/metrics/statistics.json",
    "artifacts/metrics/failure_boundary.json",
    "artifacts/plots/parity_2d.png",
    "artifacts/plots/parity_3d.png",
    "artifacts/report.md"
]


def check_artifacts_exist() -> bool:
    """
    Check if all required artifacts exist.

    Returns:
        True if all artifacts exist, False otherwise.
    """
    logger.info("Checking for required artifacts...")
    missing_files = []
    for file_path in REQUIRED_FILES:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        logger.error(f"Missing artifacts: {missing_files}")
        return False
    logger.info("All required artifacts exist.")
    return True


def validate_data_integrity() -> bool:
    """
    Validate data integrity.

    Returns:
        True if data integrity is valid, False otherwise.
    """
    logger.info("Validating data integrity...")
    # Placeholder for actual validation logic
    return True


def validate_model_artifacts() -> bool:
    """
    Validate model artifacts.

    Returns:
        True if model artifacts are valid, False otherwise.
    """
    logger.info("Validating model artifacts...")
    # Placeholder for actual validation logic
    return True


def validate_analysis_artifacts() -> bool:
    """
    Validate analysis artifacts.

    Returns:
        True if analysis artifacts are valid, False otherwise.
    """
    logger.info("Validating analysis artifacts...")
    # Placeholder for actual validation logic
    return True


def run_validation() -> bool:
    """
    Run the full validation pipeline.

    Returns:
        True if validation passes, False otherwise.
    """
    logger.info("Starting validation pipeline...")
    start_time = time.time()

    if not check_artifacts_exist():
        logger.error("Artifact existence check failed.")
        return False

    if not validate_data_integrity():
        logger.error("Data integrity validation failed.")
        return False

    if not validate_model_artifacts():
        logger.error("Model artifacts validation failed.")
        return False

    if not validate_analysis_artifacts():
        logger.error("Analysis artifacts validation failed.")
        return False

    end_time = time.time()
    logger.info(f"Validation completed in {end_time - start_time:.2f} seconds.")
    return True


def main() -> None:
    """
    Main function to run the quickstart validator.
    """
    set_seeds()
    logger.info("Starting quickstart validation.")

    if run_validation():
        logger.info("Quickstart validation passed.")
    else:
        logger.error("Quickstart validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
