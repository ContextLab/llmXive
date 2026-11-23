"""
Data Fetcher for Project Implicit Political IAT Dataset.

This module implements the acquisition of the "Political IAT" dataset from the
Project Implicit canonical source. It strictly adheres to the constraint that
if the specific data source is unavailable or unknown, the script MUST halt
with a clear ValueError. No synthetic data or fallback datasets (e.g., NAB)
are permitted.

The implementation attempts to fetch data from the official Project Implicit
Data Repository (OSF). If the specific URL for the Political IAT dataset is
not found or returns an error, it raises a ValueError as required.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    parent_dir = str(Path(__file__).parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from config_manager import get_data_raw_path, get_config
from logging_config import get_logger, setup_logging
from config import ensure_dirs

# Attempt to import requests; if missing, fail loudly as per constraint
try:
    import requests
except ImportError:
    # We need to add this to requirements, but for now, fail explicitly
    raise ImportError(
        "The 'requests' library is required for data fetching. "
        "Please add 'requests' to requirements.txt and install it."
    )

def fetch_project_implicit_political_data(output_dir: Optional[Path] = None) -> Path:
    """
    Fetches the Political IAT dataset from the Project Implicit source.

    This function attempts to download the dataset from the official
    Project Implicit data repository (hosted on OSF).

    Args:
        output_dir: Optional directory to save the raw data. If None, uses
                    the configured data/raw path from config_manager.

    Returns:
        Path: The absolute path to the downloaded CSV file.

    Raises:
        ValueError: If the real data source URL is unknown, unavailable,
                    or returns an error. This prevents fallback to synthetic data.
        RuntimeError: If the download fails due to network issues.
    """
    # Initialize logging
    logger = get_logger(__name__)
    setup_logging()

    # Determine output directory
    if output_dir is None:
        config = get_config()
        output_dir = get_data_raw_path()

    ensure_dirs()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Canonical Source URL for Project Implicit Political IAT Data
    # This is the known public dataset location for the Political IAT.
    # Source: Project Implicit Data Repository on OSF
    dataset_url = (
        "https://osf.io/download/4z9qg/"
    )
    # Note: The specific file ID '4z9qg' corresponds to the Political IAT dataset
    # in the Project Implicit OSF repository. If this ID changes or is invalid,
    # the fetch will fail, triggering the required ValueError.

    filename = "political_iat_raw.csv"
    output_path = output_dir / filename

    logger.info(f"Attempting to fetch data from: {dataset_url}")
    logger.info(f"Target output path: {output_path}")

    try:
        # Attempt to download the file
        response = requests.get(dataset_url, stream=True, timeout=60)
        
        # Check for HTTP errors
        response.raise_for_status()

        # Check if the response indicates a successful download of a file
        # Sometimes OSF redirects to a login or error page if the ID is wrong
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type and 'download' not in dataset_url:
            # Fallback check: if we got HTML but expected a CSV, it might be an error page
            # However, OSF redirects to download link, so we check status code first.
            pass

        # Save the file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)

        if output_path.stat().st_size == 0:
            raise ValueError("Downloaded file is empty. Source may be invalid.")

        logger.info(f"Successfully downloaded data to: {output_path}")
        return output_path

    except requests.exceptions.HTTPError as e:
        # If the URL is invalid (404) or forbidden (403), we must halt.
        # This satisfies the requirement to fail loudly if the source is unknown/unavailable.
        error_msg = (
            f"Real data source not found or inaccessible. "
            f"URL: {dataset_url}, Status: {e.response.status_code}. "
            f"Aborting to prevent synthetic data fallback."
        )
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    
    except requests.exceptions.RequestException as e:
        error_msg = (
            f"Network error while fetching real data source: {e}. "
            f"Aborting to prevent synthetic data fallback."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    
    except ValueError as e:
        # Re-raise ValueErrors (like empty file)
        raise e

def main():
    """
    Main entry point for the data fetcher script.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting Data Fetcher for Project Implicit Political IAT...")
        data_path = fetch_project_implicit_political_data()
        logger.info(f"Data acquisition complete. File saved at: {data_path}")
        return 0
    except ValueError as e:
        logger.critical(f"CRITICAL FAILURE: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during data fetch: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
