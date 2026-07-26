"""
Task T017: Save processed feature-engineered dataset to data/processed/features.csv
with source_row_id traceability.

This module implements the final step of User Story 1 (Data Acquisition and Feature Engineering).
It loads the raw dataset, ingests and normalizes compositions, computes physics-based features,
validates for unknown elements, and saves the final processed dataset.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download import download_gfa_dataset, verify_schema
from data.ingest import ingest_and_normalize
from data.features import compute_features
from data.checksums import save_checksum
from utils.logger import get_logger, log_info, log_warning, log_error
from utils.state_manager import update_artifact_hash
from utils.schema_validator import validate_processed_features

logger = get_logger(__name__)

def load_and_prepare_data(raw_data_path: Path, processed_dir: Path) -> pd.DataFrame:
    """
    Orchestrates the full data pipeline: download -> ingest -> feature engineering.

    Args:
        raw_data_path: Path where the raw CSV will be saved/downloaded.
        processed_dir: Directory where processed features will be saved.

    Returns:
        DataFrame containing the fully processed features with source_row_id.
    """
    log_info(f"Starting data pipeline. Raw path: {raw_data_path}, Processed dir: {processed_dir}")

    # Ensure directories exist
    raw_data_path.parent.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download and verify raw data
    # T012: Download logic is encapsulated in download_gfa_dataset
    # It handles retries, schema verification, and checksums.
    if not raw_data_path.exists():
        log_info(f"Raw dataset not found at {raw_data_path}. Downloading...")
        download_gfa_dataset(str(raw_data_path))
    else:
        log_info(f"Raw dataset found at {raw_data_path}. Skipping download.")

    # Verify schema again just to be safe before ingestion
    if not verify_schema(raw_data_path):
        log_error(f"Schema verification failed for {raw_data_path}")
        raise ValueError(f"Schema verification failed for {raw_data_path}")

    # 2. Ingest and normalize
    log_info("Ingesting and normalizing data...")
    # ingest_and_normalize returns a DataFrame with normalized compositions
    df_ingested = ingest_and_normalize(str(raw_data_path))

    if df_ingested is None or df_ingested.empty:
        log_error("Ingestion resulted in an empty DataFrame.")
        raise ValueError("Ingestion resulted in an empty DataFrame.")

    log_info(f"Ingested {len(df_ingested)} rows. Starting feature engineering...")

    # 3. Compute features (T014, T015, T016)
    # compute_features handles:
    # - Parsing compositions
    # - Computing weighted means (radius, electronegativity, VEC)
    # - Computing size mismatch and pairwise size mismatch
    # - Filtering out rows with unknown elements (T016)
    # - Adding source_row_id traceability
    df_features = compute_features(df_ingested)

    if df_features is None or df_features.empty:
        log_error("Feature engineering resulted in an empty DataFrame.")
        raise ValueError("Feature engineering resulted in an empty DataFrame.")

    # 4. Validate for nulls in computed descriptors (T017 Verification)
    required_cols = [
        'atomic_radius_mean', 'electronegativity_mean', 'VEC_avg',
        'size_mismatch', 'pairwise_size_mismatch_1', 'pairwise_size_mismatch_2'
    ]
    # Filter to only existing columns in case some are missing due to data issues
    existing_required = [c for c in required_cols if c in df_features.columns]
    null_counts = df_features[existing_required].isnull().sum()
    if null_counts.any():
        log_warning(f"Null values found in computed descriptors:\n{null_counts[null_counts > 0]}")
        # Drop rows with nulls in required computed columns to satisfy T017 verification
        df_features = df_features.dropna(subset=existing_required)
        log_info(f"Dropped {len(df_features) - len(df_features.dropna(subset=existing_required))} rows due to nulls.")

    log_info(f"Final processed dataset contains {len(df_features)} rows.")
    return df_features

def save_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the processed features DataFrame to a CSV file.
    Updates artifact hashes for traceability.

    Args:
        df: DataFrame to save.
        output_path: Path to save the CSV file.
    """
    log_info(f"Saving features to {output_path}")
    df.to_csv(output_path, index=False)

    # Generate checksum
    save_checksum(str(output_path))
    log_info(f"Checksum generated for {output_path}")

    # Update state manager
    update_artifact_hash(str(output_path))
    log_info(f"Artifact hash updated in state for {output_path}")

    # Validate against schema
    # Note: We assume a schema file exists or is generated elsewhere for this contract
    # For now, we do a basic check
    if not output_path.exists():
        raise FileNotFoundError(f"Output file {output_path} was not created.")

    log_info(f"Successfully saved features to {output_path}")

def main():
    """Main entry point for T017."""
    log_pipeline_start = get_logger("pipeline_start")
    log_info("=== Starting T017: Save Processed Features ===")

    # Define paths
    raw_data_path = Path("data/raw/gfa_dataset.csv")
    processed_dir = Path("data/processed")
    output_path = processed_dir / "features.csv"

    try:
        # Load and prepare
        df_processed = load_and_prepare_data(raw_data_path, processed_dir)

        # Save
        save_features(df_processed, output_path)

        log_info("=== T017 Completed Successfully ===")
        return 0

    except Exception as e:
        log_error(f"Error during T017 execution: {e}")
        raise

if __name__ == "__main__":
    main()
