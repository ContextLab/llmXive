"""
Download Kepler DR25 Planet Table from MAST.

Fetches the Kepler DR25 Planet Table (MAST Product ID: kplr_dr25_planet)
using astroquery.mast with retry logic, and saves the result to
data/raw/dr25_raw.csv.
"""
import os
import sys
import logging
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
    
    # Define the specific query logic to be wrapped by retry
    def do_query():
        # Query the MAST archive for the specific product
        # Observations.download_table is a helper that can fetch specific product data
        # However, astroquery.mast usually works by searching for products then downloading
        # The most robust way for a specific curated table like DR25 Planet Table:
        
        # 1. Search for the product
        product_uri = f"mast:Kepler/product/{MAST_PRODUCT_ID}"
        
        # Search for the product URI
        query_str = f"product_uri:{product_uri}"
        results = Observations.query_criteria(product_uri=product_uri)
        
        if results is None or len(results) == 0:
            # Fallback: try searching by product name if URI query fails
            logger.warning("Direct URI query returned no results, trying alternative search.")
            results = Observations.query_criteria(product_name=MAST_PRODUCT_ID)
        
        if results is None or len(results) == 0:
            raise RuntimeError(f"Could not find product {MAST_PRODUCT_ID} on MAST.")
        
        # Download the data
        # download_table returns a path to the downloaded file
        # We need to handle the case where it might download a zip or a single file
        product_path = Observations.download_table(
            data_product=results.iloc[0],
            download_dir=str(Path(DATA_RAW_DIR).resolve())
        )
        
        return product_path

    # Execute with retry logic using exponential backoff
    # retry_call is imported from utils.retry and implements the backoff strategy
    # max_retries=5, base_delay=2.0 ensures we handle temporary API unavailability
    result_path = retry_call(do_query, max_retries=5, base_delay=2.0)
    
    if not result_path:
        raise RuntimeError("Download returned no path.")
    
    # Handle potential zip files if the download returned a zip
    # astroquery.download_table usually returns the path to the file directly if it's a single file
    # or a list of paths if multiple.
    
    # If it's a list, take the first one (should be the main table)
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
    
    # Clean up the temporary download file if it was created in a temp dir
    # But since we specified download_dir, it's in data/raw. 
    # We might want to rename it to the standard name if it has a weird name.
    target_path = Path(DATA_RAW_DIR) / OUTPUT_FILENAME
    
    if file_path != target_path:
        # Move/Rename
        import shutil
        shutil.move(file_path, target_path)
        logger.info(f"Renamed downloaded file to {OUTPUT_FILENAME}")
    else:
        logger.info(f"Downloaded file is already named {OUTPUT_FILENAME}")
    
    return df

def main():
    """Main entry point for the download script."""
    logger.info("Starting Kepler DR25 Planet Table download.")
    
    # Ensure directories exist
    initialize_directories()
    
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