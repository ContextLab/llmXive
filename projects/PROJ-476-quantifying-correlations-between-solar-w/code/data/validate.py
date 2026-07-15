"""
Data validation logic for solar wind and solar-geomagnetic data.

This module provides functions to validate DataFrame columns against
expected ACE and NOAA variable sets. It enforces strict header matching
for ACE Level 2 data to ensure data integrity before processing.
"""
import pandas as pd
from code.config import ACE_VARS, NOAA_VARS
from code import logger


def validate_columns(df: pd.DataFrame, required_cols: list) -> None:
    """
    Validate that a DataFrame contains all required columns.

    This function checks the actual headers of the provided DataFrame
    against the hardcoded list of required columns. If any column is
    missing, it logs the specific missing variable name and raises a
    ValueError with the exact format required by SC-002 and T007.

    Args:
        df: The pandas DataFrame to validate (typically raw fetched data).
        required_cols: A list of column names that must be present.
                       For ACE data, this should be ACE_VARS.
                       For NOAA data, this should be NOAA_VARS.

    Raises:
        ValueError: If any required column is missing. The error message
                    will be exactly "Missing required variable: <name>"
                    where <name> is the first missing variable found.
    """
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing variable: {col}")
            raise ValueError(f"Missing required variable: {col}")


def validate_ace_raw(df: pd.DataFrame) -> None:
    """
    Validate raw ACE Level 2 data against the strict required variables.

    This function explicitly checks the source file headers against the
    hardcoded ACE Level 2 names ('N_p', 'T_p', 'He2+_ratio') BEFORE any
    mapping or processing occurs. It satisfies FR-006 and SC-002 by
    aborting the pipeline with a clear, specific error message if the
    expected variables are missing.

    Args:
        df: The pandas DataFrame containing raw ACE data.

    Raises:
        ValueError: If 'N_p', 'T_p', or 'He2+_ratio' are missing.
                    The error message will be "Missing required variable: <name>"
                    where <name> is the specific missing variable.
    """
    logger.info("Validating ACE raw data headers against required variables...")
    # Explicitly check the hardcoded list of ACE Level 2 variables
    # This ensures we abort BEFORE any mapping or transformation
    validate_columns(df, ACE_VARS)
    logger.info("ACE raw data validation passed.")


def validate_noaa_raw(df: pd.DataFrame) -> None:
    """
    Validate raw NOAA data against the required variables.

    This function checks for the presence of NOAA variables ('Kp', 'Dst').

    Args:
        df: The pandas DataFrame containing raw NOAA data.

    Raises:
        ValueError: If 'Kp' or 'Dst' are missing.
    """
    logger.info("Validating NOAA raw data headers against required variables...")
    validate_columns(df, NOAA_VARS)
    logger.info("NOAA raw data validation passed.")