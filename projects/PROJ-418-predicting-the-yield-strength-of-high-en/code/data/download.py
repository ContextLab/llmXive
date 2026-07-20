import os
import sys
import pandas as pd
from typing import Optional
from utils.logging import get_logger
from utils.config import get_config

logger = get_logger(__name__)

# Error code constant
DATA_SOURCE_MISSING = 1

def download_dataset(url: Optional[str] = None) -> pd.DataFrame:
    """
    Fetches the HEA composition dataset from the verified URL.
    
    Args:
        url: Optional override URL. If None, reads from config (research.verified_datasets).
    
    Returns:
        DataFrame containing the raw dataset.
    
    Raises:
        RuntimeError: If no URL is provided or found in config, exits with DATA_SOURCE_MISSING.
        ValueError: If the URL format is unsupported or download fails.
    """
    if url is None:
        config = get_config()
        # Explicitly fetch from the verified_datasets mapping as per spec
        if 'research' in config and 'verified_datasets' in config['research']:
            dataset_key = 'hea_compositions'
            if dataset_key in config['research']['verified_datasets']:
                url = config['research']['verified_datasets'][dataset_key]
            else:
                raise RuntimeError(
                    f"DATA_SOURCE_MISSING: Key '{dataset_key}' not found in "
                    "research.verified_datasets in config."
                )
        else:
            raise RuntimeError(
                "DATA_SOURCE_MISSING: 'research.verified_datasets' not found in config."
            )
    
    logger.info(f"Downloading dataset from: {url}")
    
    # Ensure raw directory exists
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/hea_compositions.csv"
    
    try:
        # Attempt to read directly from URL using pandas
        df = pd.read_csv(url)
        # If successful, save to local raw directory for reproducibility
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset downloaded and saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to download dataset from {url}: {e}")
        raise RuntimeError(f"Failed to download dataset: {e}") from e
    
    return df

def main():
    """
    Entry point for the downloader script.
    """
    try:
        df = download_dataset()
        print(f"Downloaded {len(df)} rows.")
    except RuntimeError as e:
        if "DATA_SOURCE_MISSING" in str(e):
            print(f"Error: {e}")
            sys.exit(DATA_SOURCE_MISSING)
        else:
            raise

if __name__ == "__main__":
    main()
