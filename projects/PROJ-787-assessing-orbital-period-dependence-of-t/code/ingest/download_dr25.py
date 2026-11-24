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
from utils.retry import retry_call
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

    # Ensure required directories exist
    initialize_directories()

    def do_query():
        """
        Perform the actual MAST query and download.
        Returns the path to the downloaded file.
        """
        # Build the product URI for precise lookup
        product_uri = f"mast:Kepler/product/{MAST_PRODUCT_ID}"
        results = Observations.query_criteria(product_uri=product_uri)

        if results is None or len(results) == 0:
            logger.warning("Direct URI query returned no results, trying alternative search.")
            results = Observations.query_criteria(product_name=MAST_PRODUCT_ID)

        if results is None or len(results) == 0:
            raise RuntimeError(f"Could not find product {MAST_PRODUCT_ID} on MAST.")

        download_dir = Path(DATA_RAW_DIR).resolve()
        product_path = Observations.download_table(
            data_product=results.iloc[0],
            download_dir=str(download_dir)
        )
        return product_path

    # Execute the query with retry logic (max 5 attempts, exponential backoff)
    result_path = retry_call(do_query, max_retries=5, base_delay=2.0)

    if not result_path:
        raise RuntimeError("Download returned no path.")

    # Normalize result_path to a single file path
    if isinstance(result_path, list):
        if len(result_path) == 0:
            raise RuntimeError("Download returned empty list.")
        file_path = result_path[0]
    else:
        file_path = result_path

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Downloaded file not found at {file_path}")

    logger.info(f"Successfully downloaded file to {file_path}")

    # Load into DataFrame (assumes CSV format)
    df = pd.read_csv(file_path)

    # Define the final target location
    target_path = Path(DATA_RAW_DIR) / OUTPUT_FILENAME

    # Move/rename the file to the expected location if necessary
    if file_path.resolve() != target_path.resolve():
        # Ensure the target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(target_path))
        logger.info(f"Moved downloaded file to {target_path}")
    else:
        logger.info(f"Downloaded file already at target location {target_path}")

    # Also write the DataFrame explicitly as CSV to guarantee the file exists
    df.to_csv(target_path, index=False)
    logger.info(f"Wrote DataFrame to CSV at {target_path}")

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
