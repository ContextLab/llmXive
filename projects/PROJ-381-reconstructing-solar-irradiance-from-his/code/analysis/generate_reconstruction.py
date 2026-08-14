import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd

from config import ensure_directories
from models.predict import run_prediction_pipeline, save_reconstruction
from data.preprocessing import load_raw_data, merge_datasets

logger = logging.getLogger(__name__)

def run_reconstruction_generation() -> Tuple[Path, Dict[str, Any]]:
    """
    Generates the TSI reconstruction for the pre-satellite era (1610–2002).

    This function orchestrates the loading of pre-satellite GSN data,
    applies the trained models (including the Cycle-Agnostic fallback for
    unseen cycles), calculates uncertainty bounds, and saves the result
    to the specified parquet file.

    Returns:
        Tuple containing the path to the generated parquet file and a summary dict.
    """
    logger.info("Starting pre-satellite reconstruction generation (T022)...")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path("data/processed/reconstruction_1610_2002.parquet")
    
    # The heavy lifting is delegated to the prediction pipeline which handles:
    # 1. Loading pre-satellite GSN data (historical–pre-satellite era).
    # 2. Applying trained RF/GP model for known cycles.
    # 3. Applying Cycle-Agnostic fallback model for unseen cycles.
    # 4. Generating prediction intervals for uncertainty bands.
    
    reconstruction_df, metrics = run_prediction_pipeline(
        start_year=1610,
        end_year=2002,
        output_path=output_path
    )
    
    summary = {
        "output_path": str(output_path),
        "rows_generated": len(reconstruction_df),
        "time_range": f"{reconstruction_df['date'].min()} to {reconstruction_df['date'].max()}",
        "metrics": metrics
    }
    
    logger.info(f"Reconstruction saved to {output_path}")
    logger.info(f"Generated {summary['rows_generated']} rows.")
    
    return output_path, summary

def main():
    """Entry point for running the reconstruction generation as a script."""
    logging.basicConfig(level=logging.INFO)
    try:
        path, summary = run_reconstruction_generation()
        print(f"Success: {summary}")
    except Exception as e:
        logger.error(f"Failed to generate reconstruction: {e}")
        raise

if __name__ == "__main__":
    main()