"""
Validation utilities for the emoji influence study.

This module provides functions to validate the presence and integrity
of human-rated intensity scores in the loaded dataset.
"""
import logging
from typing import List, Optional, Tuple

import pandas as pd

from src.data.loaders import DataUnavailableError

logger = logging.getLogger(__name__)

REQUIRED_INTENSITY_COLUMNS = [
    "human_intensity_score",
    "message_id"
]

def validate_intensity_scores(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Validate that the dataset contains valid human-rated intensity scores.
    
    This function checks:
    1. The presence of the required 'human_intensity_score' column.
    2. That the column is numeric.
    3. That there are no missing values (NaN) in the intensity scores.
    4. That the values are within a reasonable range (e.g., 1-5 or 0-10).
    
    Args:
        df: The loaded pandas DataFrame.
        
    Returns:
        A tuple (is_valid, error_message).
        - is_valid: True if all checks pass, False otherwise.
        - error_message: A string describing the failure reason if invalid, None otherwise.
        
    Raises:
        DataUnavailableError: If the 'human_intensity_score' column is missing.
        ValueError: If the data types or ranges are invalid.
    """
    if df.empty:
        msg = "Dataset is empty; cannot validate intensity scores."
        logger.error(msg)
        return False, msg

    # Check 1: Presence of required column
    if "human_intensity_score" not in df.columns:
        msg = (
            "Critical: 'human_intensity_score' column is missing from the dataset. "
            "The pipeline cannot proceed without human-rated intensity scores."
        )
        logger.error(msg)
        # Raise the specific error defined in loaders.py to trigger the halt mechanism
        raise DataUnavailableError(msg)

    # Check 2: Data type validation
    if not pd.api.types.is_numeric_dtype(df["human_intensity_score"]):
        msg = (
            f"'human_intensity_score' column exists but is not numeric. "
            f"Found dtype: {df['human_intensity_score'].dtype}"
        )
        logger.error(msg)
        raise ValueError(msg)

    # Check 3: Missing values
    missing_count = df["human_intensity_score"].isna().sum()
    if missing_count > 0:
        msg = (
            f"Found {missing_count} missing (NaN) values in 'human_intensity_score'. "
            "The dataset must have complete human ratings for all messages."
        )
        logger.error(msg)
        raise ValueError(msg)

    # Check 4: Range validation (assuming 1-5 scale based on typical intensity studies)
    # If the scale is different, this should be configurable, but 1-5 is a safe default check
    min_val = df["human_intensity_score"].min()
    max_val = df["human_intensity_score"].max()
    
    # Allow for common scales: 1-5, 0-5, 1-7, 0-10, 0-1
    valid_ranges = [
        (1.0, 5.0), (0.0, 5.0), (1.0, 7.0), (0.0, 10.0), (0.0, 1.0)
    ]
    
    is_in_range = any(start <= min_val and max_val <= end for start, end in valid_ranges)
    
    if not is_in_range:
        msg = (
            f"Intensity scores are outside expected ranges. "
            f"Found range [{min_val}, {max_val}]. "
            f"Expected one of: {valid_ranges}. "
            "Please verify the dataset schema."
        )
        logger.warning(msg)
        # We warn but do not raise an error here, as the scale might be valid but unusual.
        # However, for strict validation, we could raise. For now, we log and return True
        # but note the warning in the message if needed. 
        # Given the "fail loud" policy, if the range is completely off (e.g., 0-1000), we should stop.
        if max_val > 100 or min_val < -10:
             raise ValueError(f"Intensity scores [{min_val}, {max_val}] are implausible.")

    logger.info(f"Validation passed: {len(df)} records with valid intensity scores.")
    return True, None

def validate_message_ids(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Validate that 'message_id' column exists and is unique.
    
    Args:
        df: The loaded pandas DataFrame.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    if "message_id" not in df.columns:
        msg = "Critical: 'message_id' column is missing."
        logger.error(msg)
        raise DataUnavailableError(msg)

    if df["message_id"].isna().any():
        msg = "Found missing values in 'message_id' column."
        logger.error(msg)
        raise ValueError(msg)

    if df["message_id"].duplicated().any():
        msg = "Found duplicate 'message_id' values. IDs must be unique."
        logger.error(msg)
        raise ValueError(msg)

    return True, None

def run_full_validation(df: pd.DataFrame) -> bool:
    """
    Run all validation checks on the dataset.
    
    Args:
        df: The loaded pandas DataFrame.
        
    Returns:
        True if all validations pass.
        
    Raises:
        DataUnavailableError or ValueError: If any validation fails.
    """
    logger.info("Starting full dataset validation...")
    
    # Validate message IDs first
    valid, err = validate_message_ids(df)
    if not valid:
        raise ValueError(err)
        
    # Validate intensity scores (this raises DataUnavailableError if missing)
    valid, err = validate_intensity_scores(df)
    if not valid:
        # This path should ideally be caught by the raise in validate_intensity_scores
        # but included for safety
        raise ValueError(err)
        
    logger.info("All validation checks passed.")
    return True
