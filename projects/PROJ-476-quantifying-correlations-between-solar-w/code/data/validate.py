"""
Data validation utilities for solar wind and solar wind and geomagnetic data.

This module provides functions to validate the presence of required columns
in DataFrames before processing.
"""

import pandas as pd
from typing import List

from code.config import ACE_VARS, NOAA_VARS
from code import logger


def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    """
    Validate that a DataFrame contains all required columns.

    Args:
        df: The pandas DataFrame to validate.
        required_cols: A list of column names that must be present in the DataFrame.

    Raises:
        ValueError: If any column in `required_cols` is missing from `df`.
                    The error message will be "Missing required variable: <name>"
                    for the first missing variable found.
    """
    missing = []
    for col in required_cols:
        if col not in df.columns:
            missing.append(col)

    if missing:
        # Log the specific missing variable as required by SC-002
        logger.error(f"Missing required variable: {missing[0]}")
        raise ValueError(f"Missing required variable: {missing[0]}")

    logger.info(f"Validation passed: all {len(required_cols)} required columns present.")


def validate_ace_headers(filepath: str) -> None:
    """
    Validate the headers of a downloaded ACE Level 2 file against expected names.

    This function reads the CSV header to verify the presence of 'N_p', 'T_p',
    and 'He2+_ratio' BEFORE any mapping or processing occurs. If any of these
    are missing, it logs the specific missing variable and raises a ValueError.

    Args:
        filepath: Path to the raw ACE CSV file.

    Raises:
        ValueError: If the file is missing required ACE variables.
        FileNotFoundError: If the file does not exist.
    """
    logger.info(f"Validating ACE headers in {filepath}")

    try:
        # Read only the header to check columns efficiently
        df_header = pd.read_csv(filepath, nrows=0)
        actual_cols = list(df_header.columns)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"ACE data file not found: {filepath}")
    except Exception as e:
        logger.error(f"Error reading headers from {filepath}: {e}")
        raise

    # Check against the hardcoded ACE_VARS from config (N_p, T_p, He2+_ratio)
    missing_vars = []
    for var in ACE_VARS:
        if var not in actual_cols:
            missing_vars.append(var)

    if missing_vars:
        # Log the specific missing variable name as required by SC-002
        missing_var = missing_vars[0]
        logger.error(f"Missing variable: {missing_var}")
        raise ValueError(f"Missing required variable: {missing_var}")

    logger.info("ACE header validation passed.")