"""
Module: code/processing/missing_fixation_handler.py
Task: T023 [US2] Handle missing fixation data: exclude trial from analysis and log warning (Edge Case)

This module provides utilities to detect missing or invalid fixation data within
the eye-tracking pipeline. It identifies trials where critical metrics (e.g.,
dwell time, fixation count) are NaN, None, or zero when a valid measurement is
expected, excludes them from the final analysis, and logs a structured warning.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Set
from data_models import FixationTrial
from utils.logging import get_logger

logger = get_logger(__name__)

# Columns that are critical for analysis and cannot be missing/NaN
CRITICAL_METRICS = [
    'first_fixation_prob',
    'dwell_time_ms',
    'latency_ms',
    'fixation_count'
]

def identify_missing_trials(
    df: pd.DataFrame,
    critical_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Identifies rows in the dataframe that have missing or invalid values
    in critical metric columns.

    Args:
        df: The input DataFrame containing fixation metrics.
        critical_columns: List of column names to check. Defaults to CRITICAL_METRICS.

    Returns:
        Tuple containing:
            - valid_df: DataFrame with rows containing no missing critical values.
            - invalid_df: DataFrame with rows containing missing/invalid critical values.
            - exclusion_log: List of strings describing excluded trials.
    """
    if critical_columns is None:
        critical_columns = CRITICAL_METRICS

    # Ensure columns exist
    missing_cols = [col for col in critical_columns if col not in df.columns]
    if missing_cols:
        logger.warning(f"Critical columns {missing_cols} not found in dataframe. "
                       f"Check data generation pipeline.")
        # If critical columns are missing entirely, we can't validate properly.
        # Return all as invalid to force a check upstream.
        return pd.DataFrame(), df, [f"Missing critical columns: {missing_cols}"]

    # Check for NaN or None in critical columns
    # Also check for specific invalid states if applicable (e.g., negative time)
    mask = df[critical_columns].isna().any(axis=1)

    # Additional check: sometimes data is 0 or -1 to indicate "no fixation"
    # Depending on the study design, 0 dwell time might be valid (no face seen)
    # or invalid (sensor failure). For this task, we treat NaN/None as the primary
    # "missing" indicator. If 0 is considered "missing" for a specific metric,
    # it should be handled by a specific filter function, but here we stick to
    # the definition of "missing data" (NaN/None).
    
    invalid_rows = df[mask]
    valid_rows = df[~mask]

    exclusion_log = []
    for idx, row in invalid_rows.iterrows():
        # Get Trial ID if it exists, otherwise use index
        trial_id = row.get('trial_id', f"Row_{idx}")
        missing_cols_in_row = critical_columns[row[critical_columns].isna().tolist()]
        reason = f"Missing data in columns: {missing_cols_in_row.tolist()}"
        
        log_msg = f"Excluding trial {trial_id}: {reason}"
        exclusion_log.append(log_msg)
        logger.warning(log_msg)

    if len(invalid_rows) > 0:
        logger.info(f"Total trials excluded due to missing fixation data: {len(invalid_rows)}")
    
    return valid_rows, invalid_rows, exclusion_log

def filter_and_log_missing_fixations(
    input_path: Path,
    output_path: Path,
    excluded_log_path: Optional[Path] = None
) -> int:
    """
    Reads a CSV of fixation metrics, filters out rows with missing data,
    writes the clean dataframe to a new CSV, and logs exclusions.

    Args:
        input_path: Path to the input CSV (e.g., from T021).
        output_path: Path to write the filtered CSV.
        excluded_log_path: Optional path to write a detailed exclusion log file.

    Returns:
        int: The number of rows excluded.
    """
    logger.info(f"Loading fixation data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows.")

    valid_df, invalid_df, exclusion_log = identify_missing_trials(df)

    excluded_count = len(invalid_df)
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} trials due to missing fixation data.")
        
        # Write exclusion log if path provided
        if excluded_log_path:
            excluded_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(excluded_log_path, 'w', encoding='utf-8') as f:
                f.write("# Exclusion Log for Missing Fixation Data\n")
                f.write(f"# Source: {input_path}\n")
                f.write(f"# Excluded Count: {excluded_count}\n\n")
                for entry in exclusion_log:
                    f.write(f"{entry}\n")
            logger.info(f"Exclusion log written to {excluded_log_path}")
    else:
        logger.info("No missing fixation data detected. All trials valid.")

    # Write the valid dataframe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data written to {output_path} ({len(valid_df)} rows).")

    return excluded_count

def main():
    """
    Entry point for the missing fixation handler script.
    Reads from data/interim/fixation_metrics.csv and writes to
    data/interim/fixation_metrics_cleaned.csv.
    """
    # Determine paths based on project structure
    # Assuming standard project root relative to this file location
    import os
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "interim"
    
    input_file = data_dir / "fixation_metrics.csv"
    output_file = data_dir / "fixation_metrics_cleaned.csv"
    log_file = data_dir / "missing_fixation_exclusions.log"

    if not input_file.exists():
        # Check if it's in a different location or if US2 hasn't run yet
        logger.error(f"Input file {input_file} not found. "
                     "Ensure T021 (eye_tracking.py) has run successfully.")
        return 1

    try:
        count = filter_and_log_missing_fixations(input_file, output_file, log_file)
        logger.info(f"Task T023 completed. Excluded {count} trials.")
        return 0
    except Exception as e:
        logger.error(f"Error during missing fixation handling: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
