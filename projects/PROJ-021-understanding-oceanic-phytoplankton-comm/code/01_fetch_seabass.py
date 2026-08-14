"""
Fetch SeaBASS in-situ data from HuggingFace Hub.

Source: seabass/seabass dataset on HuggingFace.
Output: data/raw/seabass.csv

This script downloads the real SeaBASS dataset, filters for relevant
columns (Chl-a, SST, Salinity), and saves the result to CSV.
It strictly adheres to the "no synthetic fallback" policy:
if the data cannot be fetched, it raises an exception.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add parent directory to path to resolve imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, setup_logging
from utils.config import get_config

# Ensure logging is configured
setup_logging()
logger = get_logger(__name__)

# Constants
DATASET_ID = "seabass/seabass"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "seabass.csv"
REQUIRED_COLUMNS = [
    "latitude", "longitude", "date", "time",
    "temp", "sal", "chl", "depth", "region", "country"
]

def fetch_seabass_data(output_path: Path) -> pd.DataFrame:
    """
    Fetch SeaBASS data from HuggingFace and save to CSV.
    
    Args:
        output_path: Path where the CSV file will be saved.
        
    Returns:
        DataFrame containing the fetched data.
        
    Raises:
        Exception: If the data cannot be fetched from the source.
    """
    logger.info(f"Fetching SeaBASS data from HuggingFace: {DATASET_ID}")
    
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install with: pip install datasets")
        raise

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load the dataset
        # Using streaming=False to ensure we get the full dataset if memory permits
        # The SeaBASS dataset is relatively small (~100MB uncompressed), so this should fit in RAM.
        logger.info("Loading dataset from HuggingFace...")
        dataset = load_dataset(DATASET_ID, split="train")
        
        logger.info(f"Dataset loaded. Rows: {len(dataset)}, Columns: {dataset.column_names}")

        # Convert to pandas DataFrame
        df = dataset.to_pandas()

        # Filter for relevant columns if they exist, otherwise keep what we have
        # and log a warning
        available_cols = [col for col in REQUIRED_COLUMNS if col in df.columns]
        if len(available_cols) < len(REQUIRED_COLUMNS):
            missing = set(REQUIRED_COLUMNS) - set(available_cols)
            logger.warning(f"Missing expected columns: {missing}. Proceeding with available columns.")
        
        df = df[available_cols]

        # Clean and preprocess data
        # Convert date/time to a single timestamp if possible
        if "date" in df.columns and "time" in df.columns:
            # Handle potential NaT or string formats
            try:
                df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce')
                df = df.drop(columns=['date', 'time'])
            except Exception as e:
                logger.warning(f"Could not parse timestamp: {e}")

        # Drop rows with critical missing values (lat, lon, chl)
        critical_cols = [col for col in ['latitude', 'longitude', 'chl'] if col in df.columns]
        if critical_cols:
            initial_count = len(df)
            df = df.dropna(subset=critical_cols)
            dropped_count = initial_count - len(df)
            if dropped_count > 0:
                logger.info(f"Dropped {dropped_count} rows due to missing critical values.")

        # Save to CSV
        logger.info(f"Saving filtered data to {output_path}")
        df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully saved {len(df)} rows to {output_path}")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch SeaBASS data: {e}")
        # Do not return a synthetic dataframe. Fail loudly.
        raise RuntimeError(f"Unable to fetch real SeaBASS data from {DATASET_ID}. Aborting.") from e

def main():
    """Main entry point for the script."""
    config = get_config()
    logger.info("Starting SeaBASS data fetch task (T011c)")
    
    try:
        df = fetch_seabass_data(OUTPUT_FILE)
        logger.info("Task T011c completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Task T011c failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
