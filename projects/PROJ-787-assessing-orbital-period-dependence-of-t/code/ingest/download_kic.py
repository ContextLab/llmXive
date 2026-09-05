"""
Download Kepler Input Catalog (KIC) v2 from MAST.

This script fetches the Kepler Input Catalog (KIC) using astroquery.mast
and saves it to data/raw/kic_raw.csv. It utilizes the retry logic defined
in code/utils/retry.py to handle transient API failures.
"""

import os
import sys
import logging
import time
from pathlib import Path
from astroquery.mast import Observations
from astropy.table import Table

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.retry import retry_with_backoff, calculate_backoff
from utils.logging_config import get_logger
from utils.setup_dirs import initialize_directories

# Configure logger for this module
logger = get_logger(__name__)

# MAST Product ID for KIC v2
# Note: The KIC is a large catalog. We attempt to fetch it via the product ID.
# If the specific 'kic_v2' product ID is not directly queryable by name in the current
# Observations interface, we fallback to searching by product name or filter criteria.
KIC_PRODUCT_ID = "kic_v2"
OUTPUT_PATH = "data/raw/kic_raw.csv"
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0


def _download_kic_product(product_uri):
    """
    Internal helper to download a file from a given URI.
    Returns the path to the downloaded file.
    """
    downloaded_files = Observations.download_by_uri(product_uri)
    
    if isinstance(downloaded_files, list):
        if len(downloaded_files) > 0:
            return downloaded_files[0]
        else:
            raise RuntimeError("Download returned an empty list.")
    else:
        return downloaded_files


def _fetch_kic_table():
    """
    Core logic to find and fetch the KIC catalog.
    
    Returns:
        astropy.table.Table: The KIC catalog data.
        
    Raises:
        RuntimeError: If the product cannot be found or downloaded.
    """
    logger.info(f"Searching MAST for product: {KIC_PRODUCT_ID}")
    
    # Strategy 1: Try querying by product ID directly
    try:
        products = Observations.query_criteria(product_id=KIC_PRODUCT_ID)
    except Exception as e:
        logger.warning(f"Query by product_id failed: {e}. Trying alternative strategies.")
        products = None
    
    # Strategy 2: Try querying by provenance name if strategy 1 failed
    if products is None or len(products) == 0:
        try:
            products = Observations.query_criteria(provenance_name=KIC_PRODUCT_ID)
        except Exception as e:
            logger.warning(f"Query by provenance_name failed: {e}.")
            products = None

    # Strategy 3: Search for "Kepler Input Catalog" if specific ID fails
    if products is None or len(products) == 0:
        logger.info("Specific ID search failed. Searching for 'Kepler Input Catalog'...")
        try:
            products = Observations.query_criteria(
                project="Kepler",
                provenance_name="KIC"
            )
        except Exception as e:
            logger.error(f"Search by project/provenance failed: {e}")
            products = None

    if products is None or len(products) == 0:
        # Final attempt: Try to find by product name pattern
        try:
            products = Observations.query_criteria(product_name="KIC")
        except Exception:
            pass

    if products is None or len(products) == 0:
        raise RuntimeError(
            f"No products found for MAST Product ID: {KIC_PRODUCT_ID} or related searches. "
            "The KIC catalog might be too large for direct query or requires a specific filter. "
            "Please check MAST availability."
        )

    # Select the first match
    # The KIC is often a single large file or a set of files.
    # We look for the dataURL.
    if 'dataURL' not in products.colnames:
        raise RuntimeError("Product found but 'dataURL' column missing.")
        
    product_uri = products['dataURL'][0]
    logger.info(f"Selected product URI: {product_uri}")

    # Download
    file_path = _download_kic_product(product_uri)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Downloaded file not found at {file_path}")

    logger.info(f"Successfully downloaded KIC to {file_path}")

    # Read the FITS table into an Astropy Table
    # KIC is typically a FITS table
    table = Table.read(file_path)
    logger.info(f"Loaded {len(table)} rows from KIC.")
    
    # Clean up the temporary FITS file if it's not the final CSV
    # We will convert to CSV immediately, so the FITS file is intermediate.
    # However, if the download returned a directory or multiple files, we need to be careful.
    # Assuming single file download for now.
    if file_path.endswith('.fits') or file_path.endswith('.fits.gz'):
        try:
            os.remove(file_path)
            logger.debug(f"Removed temporary FITS file: {file_path}")
        except OSError:
            pass

    return table


def fetch_kic_catalog():
    """
    Fetch the Kepler Input Catalog (KIC) from the MAST archive.
    
    This function wraps the core fetch logic and is intended to be passed
    to retry_with_backoff.
    
    Returns:
        astropy.table.Table: The KIC catalog data.
        
    Raises:
        RuntimeError: If the download fails after all retry attempts.
    """
    return _fetch_kic_table()


def main():
    """
    Main entry point for downloading the KIC catalog.
    """
    # Ensure directories exist
    initialize_directories()

    output_path = project_root / OUTPUT_PATH

    try:
        # Fetch the catalog with retry logic using exponential backoff
        logger.info(f"Starting KIC download with retry policy (max {MAX_RETRIES} retries)...")
        
        kic_table = retry_with_backoff(
            fetch_kic_catalog,
            exceptions=(RuntimeError, ConnectionError, OSError, TimeoutError),
            max_retries=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR
        )

        # Convert to pandas DataFrame for easier CSV handling if needed,
        # or write directly from Astropy Table.
        # Astropy Table has a write method that handles CSV well.
        logger.info(f"Writing {len(kic_table)} rows to {output_path}...")
        kic_table.write(str(output_path), format='csv', overwrite=True)

        logger.info(f"KIC catalog successfully saved to {output_path}")
        print(f"Success: KIC catalog saved to {output_path}")

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        print(f"Error: Failed to download KIC catalog. See logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
