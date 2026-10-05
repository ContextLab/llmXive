"""
Module to handle the final output of cleaned subject data.
This module implements T019: Output data/processed/subjects_cleaned.csv.
"""
import os
import sys
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    "subject_id",
    "group",
    "years_of_training",
    "age",
    "sex",
    "motion_score",
    "ses_score"
]

def write_cleaned_subjects(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    overwrite: bool = True
) -> Path:
    """
    Writes the cleaned and preprocessed subject dataframe to a CSV file.
    
    This function validates that the dataframe contains the required columns
    defined in the task specification (T019) before writing.
    
    Args:
        df: The processed pandas DataFrame containing subject data.
        output_path: Optional path to write the file. Defaults to 
                   'data/processed/subjects_cleaned.csv'.
        overwrite: If True, overwrites existing file. If False and file exists,
                 raises FileExistsError.
                 
    Returns:
        Path: The absolute path to the written file.
        
    Raises:
        ValueError: If required columns are missing from the dataframe.
        FileExistsError: If output_path exists and overwrite is False.
    """
    if output_path is None:
        output_path = Path("data/processed/subjects_cleaned.csv")
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Dataframe is missing required columns for T019 output: {missing_cols}. "
            f"Expected: {REQUIRED_COLUMNS}"
        )

    # Check for overwrite
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file {output_path} already exists.")

    # Select only required columns to ensure clean output
    # This also handles cases where extra columns might have been added during processing
    output_df = df[REQUIRED_COLUMNS].copy()

    # Sort by subject_id for deterministic output
    output_df = output_df.sort_values("subject_id").reset_index(drop=True)

    logger.info(f"Writing cleaned subjects to {output_path}...")
    logger.info(f"  - Total subjects: {len(output_df)}")
    logger.info(f"  - Musicians: {len(output_df[output_df['group'] == 'musician'])}")
    logger.info(f"  - Non-musicians: {len(output_df[output_df['group'] == 'non_musician'])}")

    output_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(output_df)} records to {output_path}")

    return output_path

def main():
    """
    Entry point for running this module as a script.
    Expects a processed dataframe to be passed via stdin (JSON) or 
    generated via the synthetic generator if in verification mode.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Output cleaned subjects to CSV (T019)")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to input CSV (processed data). If None, generates synthetic data."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/subjects_cleaned.csv",
        help="Output path for the cleaned CSV"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["verification", "analysis"],
        default="verification",
        help="Mode of operation. Verification uses synthetic data if no input provided."
    )
    args = parser.parse_args()

    df = None

    if args.input:
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input file not found: {args.input}")
        logger.info(f"Loading input data from {args.input}...")
        df = pd.read_csv(args.input)
    else:
        if args.mode == "verification":
            logger.info("No input provided in verification mode. Generating synthetic data...")
            from data.synthetic_generator import generate_synthetic_dataset
            # Generate a dataset that meets the minimum requirements (>=50 per group)
            df = generate_synthetic_dataset(n_subjects=120)
            logger.info(f"Generated {len(df)} synthetic subjects.")
        else:
            raise ValueError(
                "In analysis mode, an input file path must be provided. "
                "Use --input <path> to specify the preprocessed data."
            )

    if df is None or df.empty:
        raise ValueError("No data to process. Exiting.")

    try:
        output_path = write_cleaned_subjects(df, Path(args.output))
        print(f"SUCCESS: Output written to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to write cleaned subjects: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
