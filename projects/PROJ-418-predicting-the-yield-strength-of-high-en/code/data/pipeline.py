import os
import sys
import logging
import traceback
from typing import Optional, Dict, Any
import pandas as pd

from utils.logging import get_logger
from data.download import download_dataset
from data.preprocess import preprocess_data, normalize_units
from data.descriptors import calculate_descriptors, filter_missing_properties

logger = get_logger(__name__)

def run_pipeline(
    input_url: Optional[str] = None,
    output_csv: str = "data/processed/hea_descriptors.csv",
    skip_download: bool = False
) -> pd.DataFrame:
    """
    Orchestrates the full data pipeline:
    1. Download dataset (unless skip_download is True)
    2. Preprocess (filter single-phase, room-temp, handle missing YS)
    3. Normalize units (to MPa)
    4. Calculate descriptors (delta, dchi, VEC, entropy, melting var)
    5. Filter entries with missing elemental properties
    6. Save to CSV
    
    Args:
        input_url: URL to the dataset. If None, uses config.
        output_csv: Path to save the final processed CSV.
        skip_download: If True, assumes data exists at 'data/raw/hea_compositions.csv'.
    
    Returns:
        The processed DataFrame.
    """
    logger.info("Starting HEA Yield Strength Prediction Pipeline")
    
    # Step 1: Download
    if not skip_download:
        logger.info("Step 1: Downloading dataset...")
        raw_df = download_dataset(url=input_url)
    else:
        raw_path = "data/raw/hea_compositions.csv"
        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Skip download requested but {raw_path} not found.")
        logger.info(f"Step 1: Loading existing raw data from {raw_path}")
        raw_df = pd.read_csv(raw_path)
    
    # Step 2: Preprocess (filter single-phase, room temp, missing YS)
    logger.info("Step 2: Preprocessing data...")
    processed_df = preprocess_data(raw_df)
    
    # Step 3: Normalize units to MPa
    logger.info("Step 3: Normalizing units to MPa...")
    processed_df = normalize_units(processed_df)
    
    # Step 4: Calculate descriptors
    logger.info("Step 4: Calculating compositional descriptors...")
    # calculate_descriptors expects a DataFrame with elemental columns and YS
    df_with_descriptors = calculate_descriptors(processed_df)
    
    # Step 5: Filter missing properties
    logger.info("Step 5: Filtering entries with missing elemental properties...")
    final_df = filter_missing_properties(df_with_descriptors)
    
    # Step 6: Save to CSV
    logger.info(f"Step 6: Saving processed data to {output_csv}")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    final_df.to_csv(output_csv, index=False)
    
    logger.info(f"Pipeline complete. Saved {len(final_df)} rows to {output_csv}")
    return final_df

def main():
    """
    Main entry point for the pipeline script.
    Reads the verified dataset URL from config and runs the full pipeline.
    """
    from utils.config import get_verified_dataset_url
    
    try:
        url = get_verified_dataset_url()
        if not url:
            logger.error("No verified dataset URL found in config. Cannot proceed.")
            sys.exit(1)
        
        run_pipeline(input_url=url, output_csv="data/processed/hea_descriptors.csv")
        
        # Trigger status writer after pipeline
        from data.status_writer import main as status_main
        status_main()
        
    except Exception as e:
        logger.exception("Pipeline failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
