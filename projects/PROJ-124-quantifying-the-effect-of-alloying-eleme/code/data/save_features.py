"""
Module to save the processed feature-engineered dataset to disk.

This module implements Task T017: Save processed feature-engineered dataset
to `data/processed/features.csv` with `source_row_id` traceability.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np

# Add parent directory to path to allow relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.state_manager import update_artifact_hash
from data.ingest import ingest_and_normalize
from data.features import compute_features
from data.download import download_gfa_dataset

logger = get_logger(__name__)


def load_and_prepare_data(raw_data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw data, ingest/normalize compositions, and compute features.

    This function orchestrates the data pipeline steps:
    1. Download raw data if not present.
    2. Ingest and normalize compositions.
    3. Compute physics-based features.
    4. Validate and filter rows with unknown elements.

    Args:
        raw_data_path: Optional path to the raw CSV. If None, uses default path.

    Returns:
        A pandas DataFrame containing the processed features.
    """
    if raw_data_path is None:
        raw_data_path = Path("data/raw/gfa_dataset.csv")

    logger.info(f"Loading raw data from {raw_data_path}")

    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        logger.info("Attempting to download dataset...")
        download_gfa_dataset()
        if not raw_data_path.exists():
            raise FileNotFoundError(
                f"Raw data file {raw_data_path} does not exist after download attempt."
            )

    # Step 1: Ingest and normalize
    logger.info("Ingesting and normalizing compositions...")
    df_normalized = ingest_and_normalize(raw_data_path)

    if df_normalized.empty:
        raise ValueError("Ingested dataset is empty after normalization.")

    # Step 2: Compute features
    logger.info("Computing physics-based features...")
    df_features = compute_features(df_normalized)

    # Step 3: Validation - ensure no nulls in computed descriptors for known elements
    # The compute_features function should have already handled unknown elements,
    # but we double-check here.
    feature_cols = [
        'radius_mean', 'radius_var', 'electronegativity_mean',
        'electronegativity_var', 'VEC_raw', 'VEC_avg',
        'size_mismatch_max', 'size_mismatch_avg'
    ]
    # Add pairwise mismatch columns if they exist (dynamic based on T015)
    # We assume T015 added columns like 'pairwise_mismatch_0', 'pairwise_mismatch_1', etc.
    # or similar naming convention. We will check for any column starting with 'pairwise'.
    pairwise_cols = [col for col in df_features.columns if col.startswith('pairwise_mismatch')]
    feature_cols.extend(pairwise_cols)

    # Check for nulls
    null_counts = df_features[feature_cols].isnull().sum()
    if null_counts.sum() > 0:
        logger.warning(f"Found null values in computed features:\n{null_counts[null_counts > 0]}")
        # Drop rows with nulls in computed features
        initial_count = len(df_features)
        df_features = df_features.dropna(subset=feature_cols)
        final_count = len(df_features)
        logger.info(f"Dropped {initial_count - final_count} rows due to null feature values.")

    logger.info(f"Data preparation complete. Final row count: {len(df_features)}")
    return df_features


def save_features(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the processed feature-engineered dataset to CSV.

    This function ensures:
    1. The `source_row_id` column is present for traceability.
    2. The output directory exists.
    3. The file is written to disk.
    4. The artifact hash is updated in the state manager.

    Args:
        df: The processed DataFrame.
        output_path: Optional path for the output file. Defaults to `data/processed/features.csv`.

    Returns:
        The path to the saved file.
    """
    if output_path is None:
        output_path = Path("data/processed/features.csv")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure source_row_id exists
    if 'source_row_id' not in df.columns:
        logger.warning("source_row_id column not found. Adding index-based IDs.")
        df['source_row_id'] = df.index

    logger.info(f"Saving processed features to {output_path}")
    df.to_csv(output_path, index=False)

    # Update artifact hash for reproducibility tracking
    update_artifact_hash(str(output_path))

    logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point for the feature saving pipeline.

    Orchestrates loading, processing, and saving of the feature dataset.
    """
    try:
        logger.info("Starting feature engineering save pipeline (Task T017)...")

        # Load and prepare data
        df_processed = load_and_prepare_data()

        # Save features
        output_path = save_features(df_processed)

        # Verification
        if output_path.exists():
            logger.info(f"Verification: Output file {output_path} exists.")
            df_verify = pd.read_csv(output_path)
            logger.info(f"Verification: Loaded {len(df_verify)} rows from saved file.")

            # Check for nulls in key columns
            key_cols = ['radius_mean', 'radius_var', 'electronegativity_mean', 'VEC_avg']
            nulls = df_verify[key_cols].isnull().sum().sum()
            if nulls == 0:
                logger.info("Verification: No null values found in key descriptor columns.")
            else:
                logger.warning(f"Verification: Found {nulls} null values in key descriptor columns.")

            logger.info("Task T017 completed successfully.")
        else:
            raise FileNotFoundError(f"Failed to create output file: {output_path}")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()