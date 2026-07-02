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
