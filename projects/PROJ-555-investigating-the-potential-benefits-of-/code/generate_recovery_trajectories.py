"""
Task T028: Generate recovery_trajectories.parquet
Produces the final dataset containing deforestation event details and trajectory parameters.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

from config import ensure_directories
from logging_config import setup_logging, get_logger
from detection import generate_recovery_trajectories

# Configure logging
setup_logging()
logger = get_logger(__name__)

def main():
    """
    Main entry point for T028.
    1. Loads preprocessed NDVI and site metadata.
    2. Calls detection logic to generate trajectory parameters.
    3. Writes the final parquet file to data/processed/.
    """
    # Ensure output directories exist
    ensure_directories()

    # Define paths
    ndvi_path = Path("data/processed/ndvi_timeseries.parquet")
    metadata_path = Path("data/processed/site_metadata.csv")
    output_path = Path("data/processed/recovery_trajectories.parquet")

    # Validate inputs exist
    if not ndvi_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {ndvi_path}. "
            "Please ensure T017 (pairing and NDVI calculation) has completed."
        )
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {metadata_path}. "
            "Please ensure T017 has completed."
        )

    logger.info(f"Loading NDVI timeseries from {ndvi_path}")
    try:
        df_ndvi = pd.read_parquet(ndvi_path)
    except Exception as e:
        logger.error(f"Failed to load NDVI parquet: {e}")
        raise

    logger.info(f"Loading site metadata from {metadata_path}")
    try:
        df_meta = pd.read_csv(metadata_path)
    except Exception as e:
        logger.error(f"Failed to load site metadata CSV: {e}")
        raise

    # Merge data if necessary, or pass directly to detection function
    # The generate_recovery_trajectories function expects site-level data with NDVI history
    # We assume df_ndvi contains 'site_id' and 'date', 'ndvi' columns
    # We assume df_meta contains 'site_id' and pairing info
    
    # Perform the core logic
    logger.info("Generating recovery trajectories...")
    try:
        # The detection module's generate_recovery_trajectories function
        # handles the filtering, fitting, and parameter extraction.
        # It expects the raw timeseries data.
        df_trajectories = generate_recovery_trajectories(df_ndvi, df_meta)
    except Exception as e:
        logger.error(f"Trajectory generation failed: {e}")
        raise

    if df_trajectories.empty:
        logger.warning("No recovery trajectories were generated. The output file will be empty.")
    
    # Ensure output directory exists
    ensure_directories()
    
    # Write to parquet
    logger.info(f"Writing results to {output_path}")
    df_trajectories.to_parquet(output_path, index=False)

    logger.info(f"Task T028 complete. Output written to {output_path}")
    print(f"Generated {len(df_trajectories)} recovery trajectory records.")

if __name__ == "__main__":
    main()
