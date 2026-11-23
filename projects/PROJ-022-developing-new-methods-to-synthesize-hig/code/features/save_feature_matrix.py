"""
T026: Save feature matrix to data/processed/feature_matrix.csv

This script loads the processed feature matrix (after descriptor calculation,
encoding, and feature selection) and saves it to the specified output path.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import setup_pipeline_logger
from features.encode_synthesis_method import load_feature_matrix_or_standardized_data
from features.feature_selection import select_features

logger = setup_pipeline_logger("save_feature_matrix")

INPUT_PATH = "data/processed/standardized_polymers.csv"
OUTPUT_PATH = "data/processed/feature_matrix.csv"
METADATA_PATH = "data/processed/feature_selection_metadata.json"

def main():
    """
    Main entry point for saving the feature matrix.
    """
    logger.info(f"Starting feature matrix save process for T026")
    
    # Ensure output directory exists
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the standardized data
    logger.info(f"Loading standardized data from {INPUT_PATH}")
    try:
        df = load_feature_matrix_or_standardized_data(INPUT_PATH)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        raise

    # Perform feature selection if metadata exists
    # This ensures we save the final feature set used for modeling
    if Path(METADATA_PATH).exists():
        logger.info(f"Applying feature selection using metadata from {METADATA_PATH}")
        try:
            df_selected, _ = select_features(df)
            logger.info(f"Selected features: {len(df_selected.columns)} columns")
            df = df_selected
        except Exception as e:
            logger.error(f"Feature selection failed, saving original: {e}")
    else:
        logger.warning(f"No feature selection metadata found at {METADATA_PATH}. Saving all available features.")

    # Validate that we have a valid dataframe to save
    if df.empty:
        logger.error("Feature matrix is empty after processing. Cannot save.")
        raise ValueError("Feature matrix is empty after processing.")

    # Save to CSV
    logger.info(f"Saving feature matrix to {OUTPUT_PATH}")
    df.to_csv(OUTPUT_PATH, index=False)
    
    # Verify file was written
    if os.path.exists(OUTPUT_PATH):
        file_size = os.path.getsize(OUTPUT_PATH)
        logger.info(f"Successfully saved feature matrix: {OUTPUT_PATH} ({file_size} bytes)")
        logger.info(f"Shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
    else:
        logger.error("File was not created on disk.")
        raise RuntimeError("Failed to write output file to disk.")

    logger.info("T026 Task completed successfully.")
    return OUTPUT_PATH

if __name__ == "__main__":
    main()
