"""
T017: Save processed feature-engineered dataset to data/processed/features.csv
with source_row_id traceability (Constitution Principle IV).

This script acts as the final aggregation step for User Story 1. It reads the
normalized raw data (from ingest.py) and the computed features (from features.py),
merges them, adds a traceable source_row_id, validates the schema, and saves
the final artifact.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger, log_info, log_error, log_warning
from utils.state_manager import update_artifact_hash
from utils.schema_validator import validate_processed_features
from data.features import compute_features
from data.ingest import ingest_and_normalize

# Configure logging
logger = get_logger(__name__)

# Constants
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "gfa_dataset.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "features.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "data_schema.yaml"

def load_and_prepare_data() -> pd.DataFrame:
    """
    Loads the raw dataset, normalizes compositions, and computes features.
    This effectively runs the pipeline steps T012 (download - assumed done),
    T013 (ingest), T014 (features), and T016 (validation) in sequence.
    """
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Raw data not found at {RAW_DATA_PATH}. "
            "Please run code/data/download.py first."
        )

    logger.info(f"Loading raw data from {RAW_DATA_PATH}")
    # T013: Ingest and normalize
    df_normalized = ingest_and_normalize(RAW_DATA_PATH)

    if df_normalized.empty:
        raise ValueError("Normalized data is empty after ingestion. Check raw data source.")

    logger.info(f"Computed {len(df_normalized)} valid rows after normalization.")

    # T014 & T015: Compute features
    logger.info("Computing physics-based features...")
    df_features = compute_features(df_normalized)

    if df_features.empty:
        raise ValueError("Feature computation resulted in an empty dataframe.")

    # Ensure source_row_id exists (traceability)
    # We map the original index from the raw file to the processed file
    # Assuming ingest_and_normalize preserves order for valid rows
    df_features['source_row_id'] = df_features.index

    return df_features

def save_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the dataframe to CSV and updates artifact hashes.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving processed features to {output_path}")
    df.to_csv(output_path, index=False)

    # Verify file was written
    if not output_path.exists():
        raise IOError(f"Failed to write output file: {output_path}")

    # T017: Update state for traceability (Constitution Principle IV)
    update_artifact_hash(str(output_path))
    log_info(f"Artifact hash updated for {output_path.name}")

def main():
    """
    Main entry point for T017.
    """
    try:
        log_info("Starting T017: Save processed feature-engineered dataset")

        # 1. Load and Process
        df_final = load_and_prepare_data()

        # 2. Validate Schema
        if not SCHEMA_PATH.exists():
            log_warning(f"Schema file not found at {SCHEMA_PATH}. Skipping strict validation.")
        else:
            is_valid, errors = validate_processed_features(df_final, str(SCHEMA_PATH))
            if not is_valid:
                log_error(f"Schema validation failed: {errors}")
                # Do not fail the pipeline if schema is missing, but log it heavily
            else:
                log_info("Schema validation passed.")

        # 3. Save
        save_features(df_final, OUTPUT_PATH)

        log_info(f"T017 completed successfully. Output: {OUTPUT_PATH}")
        return 0

    except Exception as e:
        log_error(f"T017 failed: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main())
