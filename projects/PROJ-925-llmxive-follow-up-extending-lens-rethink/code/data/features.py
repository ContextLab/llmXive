"""
code/data/features.py
Wrapper script to execute feature extraction pipeline.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, init_run
from utils.logging import setup_logging, get_logger
from utils.validation import validate_feature_vector_schema
from features import extract_features_batch, main as extract_main
from utils.exclusion_processor import main as process_exclusions_main

logger = get_logger(__name__)

def main():
    """
    Orchestrates the full feature extraction pipeline:
    1. Load raw data
    2. Extract features
    3. Validate against schema
    4. Save to disk
    5. Process exclusions
    """
    setup_logging()
    logger.info("Starting Feature Extraction Pipeline (T018b)")

    paths = get_paths()

    # 1. Load raw data (reusing logic from extract_main or direct load)
    input_path = paths.raw / "pick-a-pic.parquet"
    output_path = paths.processed / "features.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Raw data not found at {input_path}. Run T009 first.")

    # 2. Extract features
    logger.info(f"Extracting features from {input_path}")
    features_df = extract_main()

    # 3. Validate against schema
    logger.info("Validating feature vector schema")
    try:
        # Load schema and validate
        validate_feature_vector_schema(features_df)
        logger.info("Schema validation passed.")
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        # Depending on strictness, we might raise or just warn.
        # Per FR-003, we should raise if missing required columns.
        raise

    # 4. Save to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")

    # 5. Process exclusions
    logger.info("Processing exclusion logs")
    process_exclusions_main()

    logger.info("Feature Extraction Pipeline complete.")
    return features_df

if __name__ == "__main__":
    main()
