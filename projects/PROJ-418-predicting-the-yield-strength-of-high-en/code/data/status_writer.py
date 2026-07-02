import os
import json
import logging
import pandas as pd
from typing import Dict, Any

from utils.logging import get_logger

logger = get_logger(__name__)


def write_data_status(
    csv_path: str,
    output_path: str,
    count_threshold: int = 500,
    power_threshold: int = 50
) -> Dict[str, Any]:
    """
    Generates a status report based on the row count of the processed HEA descriptors CSV.

    Writes a JSON file to `output_path` containing:
    - 'count': The number of rows in the CSV.
    - 'count_warning': True if count < count_threshold (500), else False.
    - 'power_status': 'insufficient_power' if count < power_threshold (50),
                      'adequate_power' otherwise.

    Args:
        csv_path: Path to the input CSV file (data/processed/hea_descriptors.csv).
        output_path: Path to the output JSON file (output/data_status.json).
        count_threshold: Threshold for data limitation warning.
        power_threshold: Threshold for statistical power insufficiency.

    Returns:
        The status dictionary written to the JSON file.
    """
    if not os.path.exists(csv_path):
        logger.error(f"Input CSV file not found: {csv_path}")
        raise FileNotFoundError(f"Input CSV file not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        count = len(df)
    except Exception as e:
        logger.error(f"Failed to read or count rows in {csv_path}: {e}")
        raise

    logger.info(f"Processed dataset contains {count} samples.")

    count_warning = count < count_threshold
    if count_warning:
        logger.warning(
            f"Data limitation warning: Sample size ({count}) is below "
            f"threshold ({count_threshold}). Model reliability may be compromised."
        )

    if count < power_threshold:
        power_status = "insufficient_power"
        logger.warning(
            f"INSUFFICIENT_POWER: N={count} < {power_threshold}. "
            f"Statistical tests (permutation, bootstrap) will be skipped."
        )
    else:
        power_status = "adequate_power"

    status = {
        "count": count,
        "count_warning": count_warning,
        "power_status": power_status,
        "thresholds": {
            "count_warning_threshold": count_threshold,
            "power_insufficient_threshold": power_threshold
        }
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)

    logger.info(f"Data status written to: {output_path}")
    return status


def main():
    """
    Main entry point for the status writer script.
    Expects the processed CSV at data/processed/hea_descriptors.csv
    and writes output to output/data_status.json.
    """
    # Define paths relative to project root
    # Assuming this script is run from the project root or code/ directory
    # We use relative paths as per project conventions
    csv_path = "data/processed/hea_descriptors.csv"
    output_path = "output/data_status.json"

    logger.info("Starting data status generation...")
    try:
        status = write_data_status(csv_path, output_path)
        logger.info(f"Status generation complete. Power Status: {status['power_status']}")
    except FileNotFoundError as e:
        logger.error(f"Terminating: {e}")
        # Exit with specific error code if data is missing
        # In a real pipeline, this might trigger a retry or alert
        import sys
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during status generation: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()