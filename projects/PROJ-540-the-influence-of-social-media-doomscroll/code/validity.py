"""
Construct validity checks to prevent mathematical coupling between variables.
"""
import pandas as pd
import numpy as np
import logging
from typing import Union, List
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def check_construct_validity(
    df: pd.DataFrame,
    var_a: str,
    var_b: str,
    correlation_threshold: float = 0.99
) -> bool:
    """
    Verify that two variables are distinct constructs and not mathematically coupled.

    This function checks:
    1. That both columns exist in the dataframe.
    2. That the variables are not identical (correlation == 1.0).
    3. That the correlation does not exceed the specified threshold (default 0.99).

    Args:
        df: The dataframe containing the variables.
        var_a: Name of the first variable (e.g., 'baseline_anxiety').
        var_b: Name of the second variable (e.g., 'anxiety_score').
        correlation_threshold: Maximum allowed correlation coefficient. Default is 0.99.

    Returns:
        True if the constructs are distinct and valid.

    Raises:
        ValueError: If required columns are missing.
        MathematicalCouplingError: If variables are identical or highly correlated.
    """
    # Check for column existence
    missing_cols = []
    if var_a not in df.columns:
        missing_cols.append(var_a)
    if var_b not in df.columns:
        missing_cols.append(var_b)

    if missing_cols:
        raise ValueError(f"Required columns missing: {missing_cols}")

    # Drop NaN values for correlation calculation
    valid_data = df[[var_a, var_b]].dropna()

    if len(valid_data) < 2:
        logger.warning(f"Insufficient data points ({len(valid_data)}) to calculate correlation between {var_a} and {var_b}.")
        return True

    # Calculate correlation
    correlation = valid_data[var_a].corr(valid_data[var_b])

    logger.info(f"Correlation between {var_a} and {var_b}: {correlation:.4f}")

    # Check for identical variables (perfect correlation)
    if np.isclose(correlation, 1.0):
        raise MathematicalCouplingError(
            f"Mathematical coupling detected: '{var_a}' and '{var_b}' are identical (r=1.0)."
        )

    # Check for high correlation exceeding threshold
    if abs(correlation) > correlation_threshold:
        raise MathematicalCouplingError(
            f"Mathematical coupling detected: '{var_a}' and '{var_b}' are too highly correlated (r={correlation:.4f} > {correlation_threshold})."
        )

    logger.info(f"Construct validity check passed for '{var_a}' and '{var_b}'.")
    return True
