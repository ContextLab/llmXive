import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

from utils.exceptions import DataQualityError
from ingestion.logging_utils import log_validation_failure, log_excluded_record

def calculate_match_proportion(df: pd.DataFrame) -> float:
    """
    Calculate the proportion of rows with valid soil data for all predictors.
    """
    predictors = ["N", "P", "K", "pH"]
    total = len(df)
    if total == 0:
        return 0.0
    
    valid = df[predictors].notna().all(axis=1).sum()
    return valid / total

def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows where all predictors are non-null.
    """
    predictors = ["N", "P", "K", "pH"]
    return df[df[predictors].notna().all(axis=1)]

def validate_soil_data_coverage(
    df: pd.DataFrame, 
    threshold: float = 0.90,
    log_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Validate that match proportion >= threshold.
    If not, raise DataQualityError.
    Logs excluded records if provided.
    """
    match_prop = calculate_match_proportion(df)
    
    if match_prop < threshold:
        error_msg = f"Match proportion {match_prop:.4f} < {threshold}. Pipeline halted."
        if log_path:
            log_validation_failure(error_msg, log_path)
        raise DataQualityError(error_msg, match_prop)
    
    logging.info(f"Validation passed: Match proportion = {match_prop:.4f}")
    return df

def main():
    """
    Main entry point for T015.
    """
    logging.info("Validation module loaded.")

if __name__ == "__main__":
    main()
