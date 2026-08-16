import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from config import get_config
from utils import setup_logging, RetrievalError
from retrieval import run_single_spectrum_retrieval, calculate_mdc, detect_low_snr_spectrum
from data_models import RetrievalResult, CensorshipStatus

logger = logging.getLogger(__name__)

def process_retrieval_results(metadata_path: str, output_path: str) -> None:
    """
    Reads metadata from data/processed/metadata.csv, runs retrieval on each spectrum,
    handles upper limits for low SNR data, and saves results to data/processed/retrieval_results.csv.

    Output columns:
    planet_name, water_mixing_ratio, uncertainty, is_upper_limit, detection_limit, min_detectable_concentration
    """
    config = get_config()
    raw_dir = Path(config['paths']['raw_data'])
    processed_dir = Path(config['paths']['processed_data'])
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    logger.info(f"Loading metadata from {metadata_path}")
    df_meta = pd.read_csv(metadata_path)
    
    results = []
    
    for idx, row in df_meta.iterrows():
        planet_name = row['planet_name']
        spectrum_file = raw_dir / f"{planet_name}.fits" # Assuming naming convention based on T012
        
        if not spectrum_file.exists():
            # Fallback for testing if file naming differs, but strictly we expect the file
            logger.warning(f"Spectrum file not found for {planet_name}: {spectrum_file}")
            continue

        try:
            # Check SNR to determine if we need upper limit logic
            snr = row['snr']
            resolution = row['resolution']
            
            is_upper_limit = False
            water_mixing_ratio = None
            uncertainty = None
            detection_limit = None
            mdc = None

            if detect_low_snr_spectrum(snr, resolution):
                logger.info(f"Low SNR detected for {planet_name} (SNR={snr}). Deriving upper limit.")
                # Derive upper limit based on noise floor
                detection_limit, mdc = calculate_mdc(snr, resolution)
                is_upper_limit = True
                # For upper limits, we set the value to the detection limit
                water_mixing_ratio = detection_limit
                uncertainty = detection_limit # Standard convention for upper limits often uses the limit as 1-sigma approx or 0
            else:
                logger.info(f"Running retrieval for {planet_name}")
                result: RetrievalResult = run_single_spectrum_retrieval(spectrum_file)
                
                water_mixing_ratio = result.water_mixing_ratio
                uncertainty = result.uncertainty
                
                # Calculate MDC even for detected values for robustness reporting
                mdc = calculate_mdc(snr, resolution)
                detection_limit = mdc * 3.0 # Approximate 3-sigma detection limit if needed, or derived from noise

            results.append({
                'planet_name': planet_name,
                'water_mixing_ratio': water_mixing_ratio,
                'uncertainty': uncertainty,
                'is_upper_limit': is_upper_limit,
                'detection_limit': detection_limit,
                'min_detectable_concentration': mdc
            })

        except Exception as e:
            logger.error(f"Failed to process {planet_name}: {e}")
            # Handle non-convergent retrievals: log failure, proceed without halting
            # We record a failure row or skip? Task says "proceed without halting". 
            # We'll record a row with NaNs to maintain alignment, or skip. 
            # Let's skip to avoid corrupting the CSV with NaNs unless specified.
            continue

    if not results:
        logger.warning("No results were generated. Check input data and retrieval logic.")
        # Create an empty file with headers to satisfy schema expectations
        output_df = pd.DataFrame(columns=[
            'planet_name', 'water_mixing_ratio', 'uncertainty', 
            'is_upper_limit', 'detection_limit', 'min_detectable_concentration'
        ])
    else:
        output_df = pd.DataFrame(results)

    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved retrieval results to {output_path}")
    logger.info(f"Total results saved: {len(output_df)}")

def main():
    config = get_config()
    metadata_path = Path(config['paths']['processed_data']) / 'metadata.csv'
    output_path = Path(config['paths']['processed_data']) / 'retrieval_results.csv'
    
    setup_logging()
    process_retrieval_results(str(metadata_path), str(output_path))

if __name__ == "__main__":
    main()
