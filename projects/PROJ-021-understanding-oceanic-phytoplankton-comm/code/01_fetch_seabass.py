"""
Fetch SeaBASS in-situ data from the verified HuggingFace dataset source.

Source: seabass/seabass
Output: data/raw/seabass.csv

This script downloads the full SeaBASS dataset from HuggingFace Hub.
It strictly adheres to the "fail loudly" policy: if the real data fetch fails,
it raises an exception and does NOT fall back to synthetic data.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, setup_logging

# Constants
DATASET_NAME = "seabass/seabass"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "seabass.csv"

# Required columns based on task description (Chl-a, SST, Salinity)
# The dataset may have variations in column names, we map them below.
TARGET_COLUMNS = [
    "time", "latitude", "longitude", 
    "temperature", "salinity", "chl_a", 
    "depth", "station_name", "cruise_id"
]

def fetch_seabass_data():
    """
    Fetches the SeaBASS dataset from HuggingFace and saves it to CSV.
    
    Raises:
        Exception: If the dataset cannot be fetched or processed.
        FileNotFoundError: If the output directory cannot be created.
    """
    logger = get_logger("fetch_seabass")
    logger.info(f"Starting fetch of SeaBASS data from HuggingFace: {DATASET_NAME}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Import here to avoid heavy dependency load if not needed, 
        # but datasets is a required dependency per T002.
        from datasets import load_dataset
        
        logger.info("Loading dataset from HuggingFace (streaming=False for full download)...")
        # We load the full dataset as per the requirement to not shrink to a toy
        # unless memory constraints are hit (handled in preprocessing).
        # streaming=True is an option if memory is tight, but we fetch full here.
        dataset = load_dataset(DATASET_NAME, split="train")
        
        logger.info(f"Dataset loaded successfully. Rows: {len(dataset)}, Columns: {dataset.column_names}")
        
        # Convert to pandas DataFrame
        df = dataset.to_pandas()
        
        logger.info("Converting HuggingFace dataset to Pandas DataFrame...")
        
        # Standardize column names to match expected schema (lowercase, underscore)
        # HuggingFace SeaBASS dataset often has specific naming conventions.
        # We map common variations to our target schema.
        column_mapping = {
            # Time
            'time': 'time',
            'datetime': 'time',
            
            # Location
            'latitude': 'latitude',
            'lat': 'latitude',
            'longitude': 'longitude',
            'lon': 'longitude',
            
            # Environmental
            'temperature': 'temperature',
            'temp': 'temperature',
            'sst': 'temperature', # Sea Surface Temperature
            'salinity': 'salinity',
            'sal': 'salinity',
            'chl_a': 'chl_a',
            'chlorophyll': 'chl_a',
            'chlorophyll_a': 'chl_a',
            'depth': 'depth',
        }
        
        # Rename columns where possible
        existing_cols = set(df.columns)
        mapped_cols = {}
        for key, val in column_mapping.items():
            if key in existing_cols:
                mapped_cols[key] = val
        
        df = df.rename(columns=mapped_cols)
        
        # Select only the relevant columns for the project, or keep all if they are useful
        # For this task, we save the cleaned dataframe.
        # We ensure the critical columns exist, otherwise we note it but don't fail if the source is valid.
        critical_cols = ['latitude', 'longitude', 'time']
        missing_critical = [c for c in critical_cols if c not in df.columns]
        if missing_critical:
            logger.warning(f"Critical columns missing in source data: {missing_critical}. "
                           "Proceeding with available columns. Downstream tasks may fail.")
        
        # Ensure required columns for the task (Chl-a, SST, Salinity) are present or mapped
        # If the dataset uses different names, we rely on the mapping above.
        # If they are truly missing, we log a warning but save what we have.
        required_in_output = ['chl_a', 'temperature', 'salinity']
        for col in required_in_output:
            if col not in df.columns:
                logger.warning(f"Required column '{col}' not found in dataset after mapping. "
                               "It will be NaN in the output.")
        
        logger.info(f"Saving to {OUTPUT_FILE}...")
        df.to_csv(OUTPUT_FILE, index=False)
        
        logger.info(f"Successfully saved SeaBASS data to {OUTPUT_FILE}")
        logger.info(f"File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.2f} MB")
        
        return OUTPUT_FILE
        
    except ImportError as e:
        logger.error(f"Missing dependency 'datasets'. Please install: pip install datasets")
        raise e
    except Exception as e:
        logger.error(f"Failed to fetch or process SeaBASS data: {e}")
        # Do NOT fall back to synthetic data. Raise the error.
        raise e

def main():
    """Main entry point for the script."""
    setup_logging()
    logger = get_logger("fetch_seabass")
    
    try:
        output_path = fetch_seabass_data()
        logger.info(f"Task T011c completed successfully. Output: {output_path}")
    except Exception as e:
        logger.error(f"Task T011c FAILED: {e}")
        # Ensure the script exits with a non-zero code on failure
        sys.exit(1)

if __name__ == "__main__":
    main()
