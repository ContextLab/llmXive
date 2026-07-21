import os
import logging
import pandas as pd
import numpy as np
from datasets import load_dataset
from pathlib import Path
from typing import Tuple, Optional
import hashlib
import time

from .logging_config import get_logger, DataIngestionError
from .utils import angular_distance

logger = get_logger(__name__)

# Constants for injection simulation
INJECTION_COUNT = 500  # Number of synthetic lenses to inject
INJECTION_SEED = 42    # Fixed seed for reproducibility
MAX_ATTEMPTS = 1000    # Max attempts to find a valid coordinate (avoid overlaps)
MIN_DIST_ARCSEC = 2.0  # Minimum distance between injections in arcseconds

def load_slfc_dataset() -> Optional[pd.DataFrame]:
    """
    Loads the Strong Lens Finding Challenge (SLFC) dataset.
    Returns a DataFrame with image metadata and labels.
    """
    logger.info("Loading SLFC dataset...")
    try:
        # Using the verified proxy dataset ID
        ds = load_dataset("astro-sim/strong-lens-finding-challenge", split="train")
        df = ds.to_pandas()
        
        # Ensure required columns exist
        required_cols = ['ra', 'dec', 'is_lens', 'snr', 'morphology']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise DataIngestionError(f"SLFC dataset missing columns: {missing}")
        
        logger.info(f"Loaded {len(df)} rows from SLFC dataset.")
        return df
    except Exception as e:
        logger.error(f"Failed to load SLFC dataset: {e}")
        raise DataIngestionError(f"Failed to load SLFC dataset: {e}") from e

def extract_real_labels(df: pd.DataFrame, output_path: str) -> None:
    """
    Extracts 'is_lens' labels from the SLFC dataset and saves them to a CSV.
    This serves as ground truth for purity calculation (FR-003).
    """
    if df is None or df.empty:
        raise DataIngestionError("Input DataFrame is empty or None.")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Select relevant columns for ground truth
    labels_df = df[['ra', 'dec', 'is_lens']].copy()
    labels_df.columns = ['RA', 'Dec', 'is_lens']
    
    logger.info(f"Saving real labels to {output_file}")
    labels_df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(labels_df)} real labels.")

def generate_injection_ground_truth(df: pd.DataFrame, output_path: str) -> None:
    """
    Injects synthetic lens images at random coordinates into the SLFC background 
    to create a ground truth catalog for injection/recovery simulation (FR-008).
    
    Saves to `data/raw/injection_ground_truth.csv` with columns:
    RA, Dec, injected_id
    
    This function ensures:
    1. Coordinates are within the dataset's RA/Dec bounds.
    2. Injected lenses are sufficiently separated (min 2.0 arcsec).
    3. A fixed random seed is used for reproducibility.
    """
    if df is None or df.empty:
        raise DataIngestionError("Input DataFrame is empty or None.")
    
    # Set seed for reproducibility
    np.random.seed(INJECTION_SEED)
    
    # Determine valid coordinate ranges from the dataset
    min_ra, max_ra = df['ra'].min(), df['ra'].max()
    min_dec, max_dec = df['dec'].min(), df['dec'].max()
    
    logger.info(f"Dataset bounds: RA [{min_ra}, {max_ra}], Dec [{min_dec}, {max_dec}]")
    
    injected_lenses = []
    attempts = 0
    max_attempts = INJECTION_COUNT * MAX_ATTEMPTS
    
    while len(injected_lenses) < INJECTION_COUNT and attempts < max_attempts:
        attempts += 1
        
        # Generate random coordinate
        new_ra = np.random.uniform(min_ra, max_ra)
        new_dec = np.random.uniform(min_dec, max_dec)
        
        # Check separation from existing injections
        is_valid = True
        for existing in injected_lenses:
            dist = angular_distance(existing['RA'], existing['Dec'], new_ra, new_dec)
            if dist < MIN_DIST_ARCSEC:
                is_valid = False
                break
        
        if is_valid:
            injected_lenses.append({
                'RA': new_ra,
                'Dec': new_dec,
                'injected_id': f"inject_{len(injected_lenses):05d}"
            })
    
    if len(injected_lenses) < INJECTION_COUNT:
        logger.warning(f"Only generated {len(injected_lenses)} injections after {attempts} attempts.")
    
    # Create DataFrame
    injection_df = pd.DataFrame(injected_lenses)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    injection_df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(injection_df)} simulated injections to {output_file}")

def main():
    """
    Main entry point for data loading and ground truth generation.
    """
    # Define paths relative to project root
    # Assuming this script is run from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    data_raw_dir = project_root / "data" / "raw"
    
    slfc_data_path = data_raw_dir / "slfc_dataset.parquet" # Placeholder if not auto-downloaded
    real_labels_path = data_raw_dir / "real_labels.csv"
    injection_path = data_raw_dir / "injection_ground_truth.csv"
    
    # Load dataset
    df = load_slfc_dataset()
    
    if df is not None:
        # T004: Extract real labels
        extract_real_labels(df, str(real_labels_path))
        
        # T006: Generate injection ground truth
        generate_injection_ground_truth(df, str(injection_path))
        
        logger.info("Data loading and ground truth generation complete.")
    else:
        logger.error("Failed to load dataset, aborting.")

if __name__ == "__main__":
    configure_logging = None
    try:
        from .logging_config import configure_logging
    except ImportError:
        pass
        
    if configure_logging:
        configure_logging()
    else:
        logging.basicConfig(level=logging.INFO)
        
    main()
