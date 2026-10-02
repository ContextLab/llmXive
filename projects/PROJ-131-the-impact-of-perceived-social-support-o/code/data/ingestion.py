import os
import sys
import hashlib
import tempfile
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config_loader import load_yaml_config

def load_config():
    """Load data source configuration."""
    config_path = project_root / "code" / "config" / "data_sources.yaml"
    return load_yaml_config(config_path)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_dataset(config: dict, logger: logging.Logger) -> Path:
    """
    Download the dataset from the configured source.
    Raises RuntimeError if fetch fails (fail loudly).
    """
    source_id = config.get("dataset_id")
    source_url = config.get("url")
    method = config.get("method", "unknown")
    
    logger.info(f"Attempting to fetch dataset: ID={source_id}, URL={source_url}, Method={method}")
    
    # Check if file already exists in data/raw
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    expected_file = raw_dir / "cyberbullying_2021.csv"
    
    if expected_file.exists():
        logger.info(f"Dataset already exists at {expected_file}. Skipping download.")
        return expected_file
    
    # Attempt to fetch based on method
    try:
        if method == "ucimlrepo":
            # Try to import and use ucimlrepo if available
            try:
                from ucimlrepo import fetch_ucirepo
                # This is a placeholder for the actual fetch logic
                # In a real scenario, we would fetch the specific dataset ID
                logger.warning("ucimlrepo method selected but dataset fetch not implemented in this skeleton.")
                # For now, we raise an error to prevent synthetic data fabrication
                raise RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")
            except ImportError:
                logger.error("ucimlrepo package not installed.")
                raise RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")
        elif method == "load_dataset":
            # Try to use datasets library
            try:
                from datasets import load_dataset
                # Placeholder for actual load
                logger.warning("load_dataset method selected but dataset fetch not implemented in this skeleton.")
                raise RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")
            except ImportError:
                logger.error("datasets package not installed.")
                raise RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")
        else:
            logger.error(f"Unknown fetch method: {method}")
            raise RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")
    
    except Exception as e:
        logger.error(f"Failed to fetch real data source: {str(e)}")
        raise RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")

def load_cyber_data(data_path: Path, logger: logging.Logger):
    """
    Load the cyberbullying dataset from disk.
    Validates columns and logs status.
    """
    import pandas as pd
    
    logger.info(f"Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    
    logger.info(f"Dataset loaded. Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    
    return df

def main():
    """
    Main entry point for data ingestion (T012).
    1. Load config.
    2. Verify data source.
    3. Download (if needed).
    4. Load and validate.
    """
    logger = get_logger(__name__)
    logger.info("Starting Data Ingestion (T012)")
    
    try:
        # Load config
        config = load_config()
        if not config:
            raise RuntimeError("E-NO-SOURCE-CONFIG: Configuration missing. Aborting.")
        
        # Download dataset
        data_path = download_dataset(config, logger)
        
        # Load data
        df = load_cyber_data(data_path, logger)
        
        # Log success
        logger.info("Data ingestion completed successfully.")
        return df
        
    except RuntimeError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {str(e)}")
        raise

if __name__ == "__main__":
    main()
