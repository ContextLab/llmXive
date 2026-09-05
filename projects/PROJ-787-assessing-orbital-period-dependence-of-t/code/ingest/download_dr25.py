"""
Download Kepler DR25 Planet Table from MAST.

Fetches the Kepler DR25 Planet Table (MAST Product ID: kplr_dr25_planet)
using astroquery.mast with retry logic, and saves the result to
data/raw/dr25_raw.csv.
"""
import os
import sys
import logging
import shutil
from pathlib import Path

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from astroquery.mast import Observations
from utils.retry import retry_call, retry_with_backoff
from utils.logging_config import get_module_logger
from utils.setup_dirs import initialize_directories
import pandas as pd

# Configure logger
logger = get_module_logger(__name__)

# Constants
MAST_PRODUCT_ID = "kplr_dr25_planet"
OUTPUT_FILENAME = "dr25_raw.csv"
DATA_RAW_DIR = "data/raw"

def fetch_dr25_planet_table():
    """
    Fetch the Kepler DR25 Planet Table from MAST.
    
    Returns:
        pd.DataFrame: The downloaded planet table.
    
    Raises:
        Exception: If the download fails after all retries.
    """
    logger.info(f"Attempting to fetch Kepler DR25 Planet Table (ID: {MAST_PRODUCT_ID})")
    
    # Ensure directories exist
    initialize_directories()
    
    # Define the specific query logic to be wrapped by retry
    def do_query():
        # Query the MAST archive for the specific product
        # The Kepler DR25 planet table is a curated product
        
        # 1. Search for the product using the product URI
        product_uri = f"mast:Kepler/product/{MAST_PRODUCT_ID}"
        
        # Use query_criteria to find the product
        # We search by product_uri to be precise
        results = Observations.query_criteria(product_uri=product_uri)
        
        if results is None or len(results) == 0:
            # Fallback: try searching by product name if URI query fails
            logger.warning("Direct URI query returned no results, trying alternative search.")
            results = Observations.query_criteria(product_name=MAST_PRODUCT_ID)
        
        if results is None or len(results) == 0:
            raise RuntimeError(f"Could not find product {MAST_PRODUCT_ID} on MAST.")
        
        # Download the data
        # download_table returns a path to the downloaded file
        # We specify the download directory explicitly
        download_dir = Path(DATA_RAW_DIR).resolve()
        
        product_path = Observations.download_table(
            data_product=results.iloc[0],
            download_dir=str(download_dir)
        )
        
        return product_path

    # Execute with retry logic using exponential backoff
    # retry_call is imported from utils.retry and implements the backoff strategy
    # max_retries=5, base_delay=2.0 ensures we handle temporary API unavailability
    result_path = retry_call(do_query, max_retries=5, base_delay=2.0)
    
    if not result_path:
        raise RuntimeError("Download returned no path.")
    
    # Handle potential list of paths if multiple files were downloaded
    if isinstance(result_path, list):
        if len(result_path) == 0:
            raise RuntimeError("Download returned empty list.")
        file_path = result_path[0]
    else:
        file_path = result_path
    
    # Ensure the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Downloaded file not found at {file_path}")
    
    logger.info(f"Successfully downloaded file to {file_path}")
    
    # Load into DataFrame
    # The Kepler DR25 planet table is typically a CSV
    df = pd.read_csv(file_path)
    
    # Determine target path
    target_path = Path(DATA_RAW_DIR) / OUTPUT_FILENAME
    
    # If the downloaded file has a different name, move/rename it
    if file_path != str(target_path):
        # If file is in a temp location or has a different name, move it
        if os.path.dirname(file_path) != str(Path(DATA_RAW_DIR).resolve()):
            shutil.move(file_path, target_path)
            logger.info(f"Moved downloaded file to {OUTPUT_FILENAME}")
        else:
            # Same directory, just rename if needed
            if os.path.basename(file_path) != OUTPUT_FILENAME:
                shutil.move(file_path, target_path)
                logger.info(f"Renamed downloaded file to {OUTPUT_FILENAME}")
    else:
        logger.info(f"Downloaded file is already at {OUTPUT_FILENAME}")
    
    return df

def main():
    """Main entry point for the download script."""
    logger.info("Starting Kepler DR25 Planet Table download.")
    
    try:
        df = fetch_dr25_planet_table()
        logger.info(f"Download complete. DataFrame shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Output saved to: {Path(DATA_RAW_DIR) / OUTPUT_FILENAME}")
    except Exception as e:
        logger.critical(f"Download process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()