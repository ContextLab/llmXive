"""
Task T012b: Validate dataset size against FR-001 target.

This script validates that the processed alloy dataset meets the minimum
sample size requirement (N >= 1000) as specified in FR-001.
"""

import logging
import sys
import os
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = os.path.join("data", "processed", "processed_alloys_raw.csv")
MIN_SAMPLES = 1000


def validate_data_availability(data_path: str, min_samples: int = 1000) -> bool:
    """
    Validate that the dataset meets the minimum sample size requirement.

    Args:
        data_path: Path to the processed alloys CSV file.
        min_samples: Minimum required number of samples (default 1000).

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the sample count is below the required threshold.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Data file not found at {data_path}. "
            "Run ingestion.py first to generate the processed data."
        )

    df = pd.read_csv(data_path)
    n_samples = len(df)

    logger.info(f"Loaded {n_samples} samples from {data_path}")

    if n_samples < min_samples:
        error_msg = (
            f"Data availability error: N = {n_samples} < {min_samples}. "
            f"Target N >= {min_samples} required by FR-001."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Data validation PASSED: N = {n_samples} >= {min_samples}")
    return True


def run_validation():
    """Main entry point for the validation script."""
    try:
        validate_data_availability(DATA_PATH, MIN_SAMPLES)
        logger.info("Validation completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_validation()
    sys.exit(exit_code)
