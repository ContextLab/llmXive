"""
T024: Implement "dimensional fidelity loss" calculation.

This module calculates the Mean Absolute Error (MAE) between the student's scalar
output and the human-annotated score for the primary dimension. It filters the
dataset to exclude samples missing critical data (primary_dimension, student_scalar,
or human annotations) and outputs the cleaned dataset and a summary of the fidelity loss.

Dependencies:
  - Uses data from code/ingest.py (data/processed/raw_data.parquet)
  - Outputs to data/processed/cleaned_data.parquet
  - Outputs summary to data/processed/fidelity_loss_summary.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the script."""
    pass  # Already configured in main or global scope


def load_raw_data(input_path: str) -> pd.DataFrame:
    """
    Load the aligned dataset from the ingestion step.

    Args:
        input_path: Path to the raw_data.parquet file.

    Returns:
        pandas DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported or empty.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading raw data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read parquet file: {e}")
        raise

    if df.empty:
        raise ValueError("Input dataset is empty.")

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df


def calculate_fidelity_loss(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate dimensional fidelity loss and filter the dataframe.

    Logic:
    1. Identify samples with missing 'primary_dimension', 'student_scalar',
       or missing human annotations for the primary dimension.
    2. Exclude these samples (marking them as 'excluded' or dropping them).
    3. For remaining samples, extract the human score for the primary dimension.
    4. Compute MAE = |student_scalar - human_score_primary| for each sample.

    Args:
        df: The input dataframe from ingestion.

    Returns:
        A filtered dataframe containing only valid samples with a new column
        'fidelity_loss' (the calculated MAE).
    """
    logger.info("Calculating dimensional fidelity loss...")

    # Create a copy to avoid modifying the original reference
    working_df = df.copy()

    # Ensure columns exist, otherwise create them with NaN to handle gracefully
    # (Though T012/T013/T014 should have handled this, we double-check)
    if 'primary_dimension' not in working_df.columns:
        logger.warning("Column 'primary_dimension' missing. Marking all as excluded.")
        working_df['excluded_reason'] = 'missing_primary_dimension'
        working_df['fidelity_loss'] = np.nan
        return working_df[working_df['excluded_reason'].isna()].copy() # Return empty if all excluded

    if 'student_scalar' not in working_df.columns:
        logger.warning("Column 'student_scalar' missing. Marking all as excluded.")
        working_df['excluded_reason'] = 'missing_student_scalar'
        working_df['fidelity_loss'] = np.nan
        return working_df[working_df['excluded_reason'].isna()].copy()

    # Filter logic:
    # 1. Exclude if primary_dimension is missing/NaN
    # 2. Exclude if student_scalar is missing/NaN
    # 3. Exclude if human_annotations is missing/NaN
    # 4. Exclude if the specific primary_dimension key is missing in human_annotations

    # Step 1: Check primary_dimension
    mask_primary = working_df['primary_dimension'].notna()
    working_df.loc[~mask_primary, 'excluded_reason'] = 'missing_primary_dimension'

    # Step 2: Check student_scalar
    mask_scalar = working_df['student_scalar'].notna()
    working_df.loc[~mask_scalar, 'excluded_reason'] = 'missing_student_scalar'

    # Step 3: Check human_annotations existence
    # Assuming human_annotations is a dict-like object or a JSON string column
    # Based on schema, it's an object. Pandas usually loads this as dict or string.
    mask_human_exists = working_df['human_annotations'].notna()
    working_df.loc[~mask_human_exists, 'excluded_reason'] = 'missing_human_annotations'

    # Step 4: Check specific dimension in human_annotations
    # We need to apply a function to check if the key exists in the dict
    def check_dimension_exists(row):
        if pd.isna(row.get('human_annotations')):
            return False
        if not isinstance(row['human_annotations'], dict):
            # If it's a string, try to parse, otherwise fail
            try:
                import json
                row['human_annotations'] = json.loads(row['human_annotations'])
            except:
                return False
        dim = row.get('primary_dimension')
        if dim and isinstance(row['human_annotations'], dict):
            return dim in row['human_annotations']
        return False

    # Apply check only to rows that passed previous checks to save time
    valid_mask = mask_primary & mask_scalar & mask_human_exists
    working_df.loc[valid_mask, 'has_primary_human_score'] = valid_mask.apply(
        lambda idx: check_dimension_exists(working_df.loc[idx]), axis=1
    )
    
    # Mark failures
    working_df.loc[~working_df['has_primary_human_score'], 'excluded_reason'] = 'missing_primary_human_score'

    # Final valid mask
    valid_final = working_df['excluded_reason'].isna()
    valid_df = working_df[valid_final].copy()

    if valid_df.empty:
        logger.warning("No valid samples found after filtering. Returning empty dataframe.")
        return valid_df

    logger.info(f"Filtered out {len(working_df) - len(valid_df)} samples. Remaining: {len(valid_df)}")

    # Calculate Fidelity Loss: |student_scalar - human_score_primary|
    def get_human_score(row):
        dim = row['primary_dimension']
        ann = row['human_annotations']
        if isinstance(ann, dict) and dim in ann:
            return float(ann[dim])
        return np.nan

    valid_df['human_score_primary'] = valid_df.apply(get_human_score, axis=1)
    
    # Handle any NaNs that slipped through (should not happen if logic is correct)
    if valid_df['human_score_primary'].isna().any():
        logger.warning("Found NaN human scores after filtering. Dropping these rows.")
        valid_df = valid_df[valid_df['human_score_primary'].notna()]

    valid_df['fidelity_loss'] = np.abs(valid_df['student_scalar'] - valid_df['human_score_primary'])

    # Clean up helper columns if desired, or keep them for debugging
    # We drop 'has_primary_human_score' as it was intermediate
    if 'has_primary_human_score' in valid_df.columns:
        valid_df.drop(columns=['has_primary_human_score'], inplace=True)

    logger.info(f"Calculated fidelity_loss for {len(valid_df)} samples.")
    return valid_df


def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleaned dataframe to a parquet file.

    Args:
        df: The processed dataframe.
        output_path: Path to save the parquet file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info("Saved successfully.")


def save_summary(df: pd.DataFrame, summary_path: str) -> None:
    """
    Calculate and save summary statistics of the fidelity loss.

    Args:
        df: The dataframe containing 'fidelity_loss'.
        summary_path: Path to save the JSON summary.
    """
    if df.empty or 'fidelity_loss' not in df.columns:
        summary = {
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "note": "No valid samples for fidelity loss calculation"
        }
    else:
        losses = df['fidelity_loss'].dropna()
        summary = {
            "count": int(len(losses)),
            "mean": float(losses.mean()) if len(losses) > 0 else None,
            "median": float(losses.median()) if len(losses) > 0 else None,
            "std": float(losses.std()) if len(losses) > 0 else None,
            "min": float(losses.min()) if len(losses) > 0 else None,
            "max": float(losses.max()) if len(losses) > 0 else None
        }

    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    logger.info(f"Saving summary to {summary_path}")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info("Summary saved successfully.")


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate dimensional fidelity loss.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the input raw data parquet file."
    )
    parser.add_argument(
        "--output-data",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to save the cleaned data."
    )
    parser.add_argument(
        "--output-summary",
        type=str,
        default="data/processed/fidelity_loss_summary.json",
        help="Path to save the fidelity loss summary JSON."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        # 1. Load Data
        df = load_raw_data(args.input)

        # 2. Calculate Fidelity Loss and Filter
        cleaned_df = calculate_fidelity_loss(df)

        # 3. Save Cleaned Data
        save_cleaned_data(cleaned_df, args.output_data)

        # 4. Save Summary
        save_summary(cleaned_df, args.output_summary)

        logger.info("Task T024 completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Task T024 failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
