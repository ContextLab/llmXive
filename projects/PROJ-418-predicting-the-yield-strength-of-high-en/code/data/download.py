"""
Data downloader module for HEA compositions dataset.
"""
import os
import sys
import pandas as pd
from typing import Optional

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.logging import get_logger
from utils.config import ensure_dataset_url_exists, get_config

logger = get_logger(__name__)

def download_dataset() -> Optional[str]:
    """
    Download the HEA compositions dataset from the verified URL.
    
    Returns:
        Path to the downloaded CSV file, or None if download failed.
    
    Raises:
        RuntimeError: If no verified URL is configured (DATA_SOURCE_MISSING).
        RuntimeError: If download fails due to network or data issues.
    """
    config = get_config()
    paths = config.get('paths', {})
    raw_data_dir = paths.get('raw_data', 'data/raw')
    os.makedirs(raw_data_dir, exist_ok=True)
    
    dataset_name = 'hea_compositions'
    
    # CRITICAL: Strictly enforce verified URL existence. 
    # No fallbacks, no local file loading, no public search.
    try:
        url = ensure_dataset_url_exists(dataset_name)
    except RuntimeError as e:
        # Log the specific missing requirement and raise with explicit error code context
        logger.error(f"DATA_SOURCE_MISSING: {str(e)}")
        raise RuntimeError(f"DATA_SOURCE_MISSING: {str(e)}") from e
    
    output_path = os.path.join(raw_data_dir, 'hea_raw.csv')
    
    try:
        logger.info(f"Downloading dataset from verified source: {url}")
        
        # Fetch data from the real URL
        df = pd.read_csv(url)
        
        # Verify we got data
        if df.empty:
            raise RuntimeError("Downloaded dataset is empty.")
        
        # Save to local raw directory
        df.to_csv(output_path, index=False)
        
        logger.info(f"Dataset downloaded successfully to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        raise RuntimeError(f"Failed to download dataset: {e}") from e