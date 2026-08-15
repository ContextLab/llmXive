import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from config import ensure_directories
from env_manager import get_data_path
from models.predict import run_prediction_pipeline, load_cycle_offsets
from models.train_fallback import load_preprocessed_data as load_fallback_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_reconstruction_generation():
    """
    Generates the TSI reconstruction for the pre-satellite era (1610-2002).
    This task implements T022 by orchestrating the prediction pipeline
    for the historical GSN data using the trained models and fallback logic.
    """
    logger.info("Starting TSI reconstruction generation for 1610-2002...")
    
    # Ensure output directories exist
    ensure_directories()
    data_path = get_data_path()
    processed_path = data_path / "processed"
    
    # Define input and output paths
    # Note: T014 produces preprocessed_data.parquet which contains the full timeline
    # We need to filter for the pre-satellite era (1610-2002)
    input_file = processed_path / "preprocessed_data.parquet"
    output_file = processed_path / "reconstruction_1610_2002.parquet"
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}. "
            "Please run T014 (preprocessing) first."
        )

    logger.info(f"Loading preprocessed data from {input_file}")
    try:
        df = pd.read_parquet(input_file)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

    # Filter for pre-satellite era (1610-2002)
    # Assuming 'date' or 'year' column exists. Based on T014, 'date' is standard.
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        pre_satellite_df = df[(df['date'].dt.year >= 1610) & (df['date'].dt.year <= 2002)].copy()
    elif 'year' in df.columns:
        pre_satellite_df = df[(df['year'] >= 1610) & (df['year'] <= 2002)].copy()
    else:
        raise ValueError("Input data must contain 'date' or 'year' column to filter by era.")

    if pre_satellite_df.empty:
        logger.warning("No data found for the 1610-2002 period in the preprocessed file.")
        # Create an empty output with correct schema if no data, or fail
        # For this task, we expect data to exist if T014 ran correctly on full history
        raise ValueError("Pre-satellite data is empty. Check preprocessing logic.")

    logger.info(f"Processing {len(pre_satellite_df)} records for reconstruction.")

    # Load cycle offsets for fallback logic (derived in T019)
    offsets_file = processed_path / "cycle_specific_coefficients.json"
    cycle_offsets = {}
    if offsets_file.exists():
        with open(offsets_file, 'r') as f:
            cycle_offsets = json.load(f)
        logger.info(f"Loaded {len(cycle_offsets)} cycle offsets for fallback correction.")
    else:
        logger.warning(f"Cycle offsets file {offsets_file} not found. Running without fallback offsets.")

    # Run the prediction pipeline
    # This function handles loading models, preparing features, and applying fallbacks
    reconstruction_df, uncertainty_df = run_prediction_pipeline(
        data=pre_satellite_df,
        cycle_offsets=cycle_offsets,
        era="pre-satellite"
    )

    # Merge results
    final_reconstruction = pd.concat([pre_satellite_df[['date', 'gsn', 'cycle_id']], reconstruction_df, uncertainty_df], axis=1)
    
    # Ensure correct dtypes
    if 'date' in final_reconstruction.columns:
        final_reconstruction['date'] = pd.to_datetime(final_reconstruction['date'])
    
    # Save to parquet
    logger.info(f"Saving reconstruction to {output_file}")
    final_reconstruction.to_parquet(output_file, index=False)

    logger.info("Reconstruction generation completed successfully.")
    return output_file

def main():
    """Entry point for the reconstruction generation script."""
    try:
        output_path = run_reconstruction_generation()
        print(f"Success: Reconstruction saved to {output_path}")
    except Exception as e:
        logger.critical(f"Reconstruction generation failed: {e}")
        raise

if __name__ == "__main__":
    main()