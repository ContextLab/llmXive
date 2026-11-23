"""
Preprocessing module for T033d: Compute Temperature-Adjusted Response Times.

This module calculates `adjusted_response_time` by subtracting a baseline
reaction time from the raw response time if baseline data is available.
If no baseline data exists, `adjusted_response_time` is set equal to
`response_time`.

It handles the logic for checking the existence of baseline data,
performing the subtraction, and logging the proportion of records
with and without baseline data.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Import logging utilities from existing project structure
try:
    from config import get_path_env_override
except ImportError:
    # Fallback if config is not in path, though it should be per T010
    pass

def setup_logging_custom(log_file=None):
    """Set up custom logging for the preprocessing script."""
    logger = logging.getLogger("preprocessing")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if called multiple times in same session
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if log_file:
            # Ensure directory exists
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute temperature-adjusted response times."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input merged dataset (Parquet)."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the adjusted dataset (Parquet)."
    )
    parser.add_argument(
        "--baseline-input",
        type=str,
        required=False,
        default=None,
        help="Optional path to the baseline reaction time dataset (CSV/Parquet)."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        required=False,
        default="results/logs/preprocessing.log",
        help="Path to the log file."
    )
    return parser.parse_args()

def load_baseline_data(baseline_path, logger):
    """
    Load baseline reaction time data.
    Returns a DataFrame if successful, None if file missing or error occurs.
    """
    if not baseline_path:
        logger.info("No baseline input path provided. Proceeding without baseline adjustment.")
        return None

    baseline_path = Path(baseline_path)
    if not baseline_path.exists():
        logger.warning(f"Baseline file not found at {baseline_path}. Proceeding without baseline adjustment.")
        return None

    try:
        if baseline_path.suffix == '.csv':
            df = pd.read_csv(baseline_path)
        elif baseline_path.suffix == '.parquet':
            df = pd.read_parquet(baseline_path)
        else:
            logger.warning(f"Unsupported baseline file format: {baseline_path.suffix}. Proceeding without baseline.")
            return None

        logger.info(f"Loaded baseline data with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load baseline data: {e}")
        return None

def merge_baseline_data(main_df, baseline_df, logger):
    """
    Merge baseline data into the main dataframe on participant_id.
    """
    if baseline_df is None:
        return main_df, False

    # Ensure participant_id is string for consistent merging
    if 'participant_id' in main_df.columns and 'participant_id' in baseline_df.columns:
        main_df['participant_id'] = main_df['participant_id'].astype(str)
        baseline_df['participant_id'] = baseline_df['participant_id'].astype(str)

        merged_df = main_df.merge(
            baseline_df[['participant_id', 'baseline_response_time']],
            on='participant_id',
            how='left'
        )
        # Check how many had a match
        matched_count = merged_df['baseline_response_time'].notna().sum()
        total_count = len(merged_df)
        match_rate = (matched_count / total_count) * 100 if total_count > 0 else 0

        logger.info(f"Merged baseline data: {matched_count}/{total_count} records ({match_rate:.2f}%) have baseline RT.")
        return merged_df, True
    else:
        logger.warning("participant_id column missing in one or both dataframes. Cannot merge baseline.")
        return main_df, False

def compute_adjusted_response_time(df, logger):
    """
    Compute adjusted_response_time = response_time - baseline_response_time.
    If baseline is missing for a row, use the raw response_time.
    """
    if 'baseline_response_time' in df.columns:
        # Calculate adjusted time
        # If baseline is NaN, the result of subtraction is NaN.
        # We want to fall back to raw response_time in that case.
        df['adjusted_response_time'] = df['response_time'] - df['baseline_response_time']
        
        # Fill NaNs in adjusted_response_time with raw response_time
        df['adjusted_response_time'] = df['adjusted_response_time'].fillna(df['response_time'])
        
        # Count records with and without baseline
        with_baseline = df['baseline_response_time'].notna().sum()
        without_baseline = df['baseline_response_time'].isna().sum()
        total = len(df)
        
        logger.info(f"Adjusted Response Time Calculation:")
        logger.info(f"  - Records with baseline: {with_baseline} ({with_baseline/total*100:.2f}%)")
        logger.info(f"  - Records without baseline (using raw RT): {without_baseline} ({without_baseline/total*100:.2f}%)")
    else:
        # No baseline column exists
        logger.info("No baseline_response_time column found. Setting adjusted_response_time = response_time.")
        df['adjusted_response_time'] = df['response_time']

    return df

def main():
    """Main entry point for T033d."""
    args = parse_args()
    logger = setup_logging_custom(args.log_file)
    
    logger.info(f"Starting T033d: Compute Temperature-Adjusted Response Times")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load main dataset
    try:
        input_path = Path(args.input)
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
        else:
            logger.error(f"Unsupported input format: {input_path.suffix}")
            sys.exit(1)
        
        logger.info(f"Loaded {len(df)} records from {args.input}")
    except Exception as e:
        logger.error(f"Failed to load input dataset: {e}")
        sys.exit(1)

    # Check for required column
    if 'response_time' not in df.columns:
        logger.error("Input dataset missing 'response_time' column.")
        sys.exit(1)

    # Load and merge baseline data
    df, baseline_available = merge_baseline_data(df, load_baseline_data(args.baseline_input, logger), logger)

    # Compute adjusted response time
    df = compute_adjusted_response_time(df, logger)

    # Save output
    try:
        if output_path.suffix == '.parquet':
            df.to_parquet(output_path, index=False)
        elif output_path.suffix == '.csv':
            df.to_csv(output_path, index=False)
        else:
            logger.error(f"Unsupported output format: {output_path.suffix}")
            sys.exit(1)
        
        logger.info(f"Successfully saved adjusted dataset to {args.output}")
    except Exception as e:
        logger.error(f"Failed to save output dataset: {e}")
        sys.exit(1)

    logger.info("T033d completed successfully.")

if __name__ == "__main__":
    main()