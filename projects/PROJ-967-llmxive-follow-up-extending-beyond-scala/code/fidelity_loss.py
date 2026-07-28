"""
T024: Implement dimensional fidelity loss calculation.

This module calculates the Mean Absolute Error (MAE) between the student's
scalar output and the human-annotated score for the primary dimension.
It filters the dataset to exclude samples with missing primary dimensions,
missing student scalars, or missing human annotations, and writes the
cleaned dataframe to disk.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def load_raw_data(input_path: str) -> pd.DataFrame:
    """
    Load the aligned raw data from parquet.
    Expects columns: prompt, image_url, teacher_scores, student_scalar,
    human_annotations, primary_dimension, excluded_reason (optional).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading raw data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def calculate_fidelity_loss(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate fidelity loss (MAE) for valid samples.
    Filters out samples where:
    - primary_dimension is missing (NaN or None)
    - student_scalar is missing (NaN or None)
    - human_annotations is missing or does not contain the primary dimension key.

    Returns a dataframe with 'fidelity_loss' column added.
    """
    logger.info("Starting fidelity loss calculation and filtering...")

    # Create a copy to avoid SettingWithCopyWarning
    clean_df = df.copy()

    # 1. Filter: Exclude samples where primary_dimension is missing
    # Check for NaN, None, or empty string
    mask_primary = clean_df['primary_dimension'].notna() & (clean_df['primary_dimension'] != '')
    if 'excluded_reason' in clean_df.columns:
        # Update existing exclusion reasons if necessary, or just filter
        clean_df = clean_df[mask_primary]
    else:
        clean_df = clean_df[mask_primary]

    logger.info(f"After filtering missing primary_dimension: {len(clean_df)} rows")

    # 2. Filter: Exclude samples where student_scalar is missing
    mask_student = clean_df['student_scalar'].notna()
    clean_df = clean_df[mask_student]
    logger.info(f"After filtering missing student_scalar: {len(clean_df)} rows")

    # 3. Filter: Exclude samples where human_annotations is missing or invalid
    # human_annotations is expected to be a dict-like object or a JSON string representation
    def is_valid_annotation(row):
        ann = row.get('human_annotations')
        if ann is None or (isinstance(ann, float) and np.isnan(ann)):
            return False
        if isinstance(ann, str):
            try:
                import json
                ann = json.loads(ann)
            except:
                return False
        if not isinstance(ann, dict):
            return False
        primary_dim = row.get('primary_dimension')
        if primary_dim and primary_dim in ann:
            return True
        return False

    mask_ann = clean_df.apply(is_valid_annotation, axis=1)
    clean_df = clean_df[mask_ann]
    logger.info(f"After filtering missing/invalid human_annotations: {len(clean_df)} rows")

    # 4. Calculate Fidelity Loss (MAE)
    # Extract the human score for the primary dimension
    def get_human_score(row):
        ann = row['human_annotations']
        if isinstance(ann, str):
            import json
            ann = json.loads(ann)
        primary_dim = row['primary_dimension']
        return ann.get(primary_dim, np.nan)

    clean_df['human_score_primary'] = clean_df.apply(get_human_score, axis=1)

    # Ensure we have valid human scores for the primary dimension
    mask_human_score = clean_df['human_score_primary'].notna()
    clean_df = clean_df[mask_human_score]
    logger.info(f"After filtering missing human score for primary dimension: {len(clean_df)} rows")

    # Calculate MAE: |student_scalar - human_score_primary|
    clean_df['fidelity_loss'] = np.abs(clean_df['student_scalar'] - clean_df['human_score_primary'])

    logger.info(f"Fidelity loss calculated. Mean: {clean_df['fidelity_loss'].mean():.4f}, Std: {clean_df['fidelity_loss'].std():.4f}")

    return clean_df

def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """
    Save the cleaned dataframe to parquet.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving cleaned data to {output_path}")
    try:
        df.to_parquet(output_path, index=False)
        logger.info("Successfully saved cleaned data.")
    except Exception as e:
        raise RuntimeError(f"Failed to save cleaned data: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate dimensional fidelity loss and clean data.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the input raw data parquet file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to save the cleaned data parquet file."
    )
    return parser.parse_args()

def main():
    args = parse_args()

    logger.info(f"Starting T024: Fidelity Loss Calculation")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")

    try:
        df = load_raw_data(args.input)
        clean_df = calculate_fidelity_loss(df)
        save_cleaned_data(clean_df, args.output)

        logger.info("T024 completed successfully.")
    except Exception as e:
        logger.error(f"T024 failed: {e}")
        raise

if __name__ == "__main__":
    main()
