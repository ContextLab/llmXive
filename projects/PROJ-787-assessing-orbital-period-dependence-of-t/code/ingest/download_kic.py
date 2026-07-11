"""
Download Kepler Input Catalog (KIC) v2 from MAST.

This script fetches the Kepler Input Catalog (KIC) using astroquery.mast
and saves it to data/raw/kic_raw.csv. It utilizes the retry logic defined
in code/utils/retry.py to handle transient API failures.
"""

import os
import sys
import logging
from pathlib import Path
from astroquery.mast import Observations
from astropy.table import Table

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.retry import retry_with_backoff
from utils.logging_config import get_logger
from utils.setup_dirs import initialize_directories

# Configure logger for this module
logger = get_logger(__name__)

# MAST Product ID for KIC v2
KIC_PRODUCT_ID = "kic_v2"
OUTPUT_PATH = "data/raw/kic_raw.csv"


def fetch_kic_catalog():
    """
    Fetch the Kepler Input Catalog (KIC) from the MAST archive.

    Returns:
        astropy.table.Table: The KIC catalog data.

    Raises:
        RuntimeError: If the download fails after all retry attempts.
    """
    logger.info(f"Attempting to fetch {KIC_PRODUCT_ID} from MAST...")

    # Define the query parameters for the KIC catalog
    # We use the Observations class to search for the product
    try:
        # Search for the product
        products = Observations.query_criteria(provenance_name=KIC_PRODUCT_ID)

        if len(products) == 0:
            # Fallback: Try searching by product ID directly if provenance_name fails
            # Sometimes the exact column name varies, try a broader search
            products = Observations.query_criteria(product_id=KIC_PRODUCT_ID)

        if len(products) == 0:
            # If still no results, try a direct product name search which is common for KIC
            # The KIC is often available as a specific dataset
            products = Observations.query_product_id(KIC_PRODUCT_ID)

        if len(products) == 0:
            raise RuntimeError(f"No products found for MAST Product ID: {KIC_PRODUCT_ID}")

        # Select the first match (usually the only one for a specific catalog version)
        product_uri = products['dataURL'][0]
        logger.info(f"Found product: {product_uri}")

        # Download the product
        # download_table returns a list of paths or a single path
        downloaded_files = Observations.download_by_uri(product_uri)

        # Handle the return value of download_by_uri
        # It can return a list of paths or a single path string depending on the version
        if isinstance(downloaded_files, list):
            if len(downloaded_files) > 0:
                file_path = downloaded_files[0]
            else:
                raise RuntimeError("Download returned an empty list.")
        else:
            file_path = downloaded_files

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Downloaded file not found at {file_path}")

        logger.info(f"Successfully downloaded KIC to {file_path}")

        # Read the FITS table into an Astropy Table
        # KIC is typically a FITS table
        table = Table.read(file_path)
        logger.info(f"Loaded {len(table)} rows from KIC.")

        return table

    except Exception as e:
        logger.error(f"Failed to fetch KIC catalog: {e}", exc_info=True)
        raise RuntimeError(f"Failed to fetch KIC catalog: {e}")


def main():
    """
    Main entry point for downloading the KIC catalog.
    """
    # Ensure directories exist
    initialize_directories()

    output_path = project_root / OUTPUT_PATH

    try:
        # Fetch the catalog with retry logic using exponential backoff
        # We wrap the main fetch function with retry logic for network issues
        kic_table = retry_with_backoff(
            fetch_kic_catalog,
            exceptions=(RuntimeError, ConnectionError, Timeout),
            max_retries=5,
            backoff_factor=2.0
        )

        # Convert to pandas DataFrame for easier CSV handling if needed,
        # or write directly from Astropy Table
        # Astropy Table has a write method that handles CSV well
        kic_table.write(str(output_path), format='csv', overwrite=True)

        logger.info(f"KIC catalog successfully saved to {output_path}")
        print(f"Success: KIC catalog saved to {output_path}")

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        print(f"Error: Failed to download KIC catalog. See logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()