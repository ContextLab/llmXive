import os
import sys
import logging
from pathlib import Path
from utils.logging_config import get_logger, set_log_level
from data.preprocess_2d import preprocess_2d
import pyarrow.parquet as pq
import pandas as pd

def main():
    """
    Orchestrates the full 2D descriptor computation pipeline and saves
    the final processed feature matrix to data/processed/descriptors.parquet.

    This script:
    1. Configures logging.
    2. Calls preprocess_2d() to handle the full pipeline (loading, descriptor
       computation, correlation filtering, NaN handling, batching).
    3. Saves the resulting DataFrame to the required Parquet artifact.
    """
    # Setup logging
    logger = get_logger(__name__)
    set_log_level(logging.INFO)

    logger.info("Starting descriptor saving pipeline (T018).")

    # Define paths
    root_dir = Path(__file__).resolve().parent.parent.parent
    raw_data_dir = root_dir / "data" / "raw"
    processed_dir = root_dir / "data" / "processed"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "descriptors.parquet"

    # Check if raw data exists (QM9 should be downloaded by T013)
    qm9_smiles_path = raw_data_dir / "qm9_smiles.csv"
    if not qm9_smiles_path.exists():
        logger.error(f"Raw data file not found: {qm9_smiles_path}. "
                     "Please run T013 (download_qm9.py) first.")
        sys.exit(1)

    try:
        # Run the preprocessing pipeline
        # preprocess_2d handles:
        # - Iterating over raw SMILES
        # - Computing 2D descriptors
        # - Filtering high correlation features (T015)
        # - Handling NaNs (T016)
        # - Batching for memory efficiency (T017)
        logger.info(f"Running preprocessing on {qm9_smiles_path}...")
        df_processed = preprocess_2d(str(qm9_smiles_path))

        if df_processed is None or df_processed.empty:
            logger.error("Preprocessing resulted in an empty DataFrame. "
                         "Check logs for specific errors during descriptor computation.")
            sys.exit(1)

        logger.info(f"Preprocessing complete. Shape: {df_processed.shape}")
        logger.info(f"Columns: {list(df_processed.columns)}")

        # Save to Parquet
        logger.info(f"Saving processed descriptors to {output_path}...")
        df_processed.to_parquet(output_path, index=False, engine='pyarrow')

        # Verify the file was created and has content
        if not output_path.exists():
            logger.error("Failed to create output file.")
            sys.exit(1)
        
        file_size = output_path.stat().st_size
        logger.info(f"Successfully saved descriptors to {output_path} ({file_size} bytes).")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("T018 completed successfully.")

if __name__ == "__main__":
    main()