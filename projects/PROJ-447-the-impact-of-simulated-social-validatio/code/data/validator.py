"""
Validator module for User Story 1 (T013).

Checks for:
1. Presence of engagement metrics, sentiment scores, and psychometric scales.
2. Distinct handling of sample size:
   - N=0: Raises DataGapError
   - 0<N<100: Raises InsufficientSampleError
3. Longitudinal ordering (engagement timestamp < self-report timestamp).
"""

import logging
from typing import Dict, Any, List

import pandas as pd

from utils.exceptions import DataGapError, InsufficientSampleError
from utils.constants import get_min_sample_size
from utils.logger import (
    get_logger,
    log_validation_start,
    log_validation_success,
    log_validation_failure,
)

logger = get_logger(__name__)

# Required columns based on the project's data model and FR-008
REQUIRED_COLUMNS = [
    "engagement_count",
    "sentiment_score",
    "self_esteem_score",
    "perceived_social_validation",
    "engagement_timestamp",
    "self_report_timestamp",
]

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate the input DataFrame against project requirements.

    Args:
        df: The DataFrame to validate.

    Returns:
        The validated DataFrame (unchanged).

    Raises:
        DataGapError: If the DataFrame is empty (N=0).
        InsufficientSampleError: If 0 < N < 100.
        ValueError: If required columns are missing or longitudinal ordering is violated.
    """
    log_validation_start()
    logger.info(f"Starting validation on dataset with {len(df)} rows.")

    # 1. Check Sample Size (Distinct Handling)
    n_rows = len(df)

    if n_rows == 0:
        logger.error("Validation failed: Dataset is empty (N=0).")
        log_validation_failure("DataGapError: Dataset is empty.")
        raise DataGapError("Dataset is empty (N=0). No data available for analysis.")

    min_sample = get_min_sample_size()
    if n_rows < min_sample:
        logger.error(
            f"Validation failed: Sample size {n_rows} is below minimum required {min_sample}."
        )
        log_validation_failure(
            f"InsufficientSampleError: Sample size {n_rows} < {min_sample}."
        )
        raise InsufficientSampleError(
            f"Sample size ({n_rows}) is insufficient for analysis. Minimum required: {min_sample}."
        )

    # 2. Check Presence of Required Columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        msg = f"Missing required columns: {missing_cols}"
        logger.error(f"Validation failed: {msg}")
        log_validation_failure(f"ValueError: {msg}")
        raise ValueError(msg)

    # 3. Check Longitudinal Ordering
    # Ensure engagement_timestamp < self_report_timestamp
    # Convert to datetime if they aren't already to ensure safe comparison
    try:
        eng_ts = pd.to_datetime(df["engagement_timestamp"])
        rep_ts = pd.to_datetime(df["self_report_timestamp"])
    except Exception as e:
        msg = f"Failed to parse timestamps for longitudinal check: {e}"
        logger.error(msg)
        log_validation_failure(f"ValueError: {msg}")
        raise ValueError(msg)

    # Identify rows where engagement happened AFTER or at the same time as self-report
    # Valid data requires engagement < self_report
    invalid_order_mask = eng_ts >= rep_ts
    invalid_count = invalid_order_mask.sum()

    if invalid_count > 0:
        msg = (
            f"Longitudinal ordering violation detected in {invalid_count} rows. "
            "Engagement timestamp must precede self-report timestamp."
        )
        logger.error(msg)
        log_validation_failure(f"ValueError: {msg}")
        raise ValueError(msg)

    logger.info("Validation passed successfully.")
    log_validation_success()
    return df

def main():
    """
    Entry point for the validator script.
    Expects a CSV file path as an argument or uses a default path.
    """
    import sys

    if len(sys.argv) < 2:
        # Default path for testing if no argument provided
        input_path = "data/processed/synthetic_data.csv"
        logger.warning(f"No input file specified. Using default: {input_path}")
    else:
        input_path = sys.argv[1]

    try:
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path)
        validate_data(df)
        logger.info("Validation completed successfully.")
    except DataGapError as e:
        logger.critical(f"Critical Data Gap: {e}")
        sys.exit(1)
    except InsufficientSampleError as e:
        logger.critical(f"Insufficient Sample: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.critical(f"Data Integrity Error: {e}")
        sys.exit(3)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(99)

if __name__ == "__main__":
    main()
