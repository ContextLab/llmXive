"""
Data Ingestion Module.
Handles loading the Cyberbullying Survey 2021 dataset from real sources.
Strictly enforces "Fail Loudly" - no synthetic fallback.
"""
import os
import sys
import hashlib
import tempfile
import logging
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config_loader import load_yaml_config

logger = get_logger(__name__)

def load_config():
    """Load the main configuration."""
    config_path = project_root / "code" / "config" / "data_sources.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    return load_yaml_config(config_path)

def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_dataset(config):
    """
    Downloads the dataset based on configuration.
    Supports 'url' or 'dataset_id' (e.g., from HuggingFace or UCI).
    """
    source_type = config.get('source_type', 'url')
    source_value = config.get('source_value') # URL or ID
    
    logger.info(f"Initiating download from {source_type}: {source_value}")
    
    # Placeholder for actual download logic based on source_type
    # In a real implementation, this would use requests, datasets.load_dataset, etc.
    # For this task, we assume the existence of a function that retrieves the data.
    # Since we cannot hardcode a specific URL that might change, we rely on the config.
    
    # We simulate the download process here by attempting to fetch from a known real source
    # if the config indicates 'huggingface' or 'uci'.
    
    # NOTE: The actual implementation of fetching real data depends on the verified source.
    # If the config points to a specific verified source (e.g., a specific HF dataset ID),
    # we use that. If not, we raise an error.
    
    if source_type == 'huggingface':
        try:
            from datasets import load_dataset
            # Streaming to handle large datasets if necessary
            ds = load_dataset(source_value, split='train', streaming=True)
            # Convert to pandas for processing (streaming might yield a generator)
            # We convert a sample or the whole thing depending on size constraints.
            # For this task, we assume we can load it or stream it.
            # To be safe and avoid OOM on small runners, we might stream and convert to DF in chunks.
            # However, for the purpose of column verification, we just need the schema or a few rows.
            # We will load the first 1000 rows to verify columns.
            import pandas as pd
            rows = []
            count = 0
            for item in ds:
                rows.append(item)
                count += 1
                if count >= 1000: # Limit for verification
                    break
            df = pd.DataFrame(rows)
            logger.info(f"Loaded {len(df)} rows from HuggingFace dataset {source_value}")
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to load dataset from HuggingFace: {str(e)}")
    elif source_type == 'url':
        # Fallback for direct URL download (e.g., CSV)
        import pandas as pd
        try:
            df = pd.read_csv(source_value)
            logger.info(f"Loaded dataset from URL: {source_value}")
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to download dataset from URL: {str(e)}")
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

def load_cyber_data():
    """
    Main entry point to load the Cyberbullying Survey 2021.
    1. Reads config.
    2. Checks if data is already in data/raw/ (optional optimization).
    3. Downloads if missing.
    4. Returns DataFrame.
    
    CRITICAL: If real fetch fails, raises RuntimeError. NO synthetic fallback.
    """
    config = load_config()
    
    # Check if source is verified
    if config.get('status') != 'verified':
        raise RuntimeError("Data source not verified. Please run T070a-Verify first.")
    
    # Attempt to load from raw data if it exists (optimization)
    raw_file = project_root / "data" / "raw" / "cyberbullying_2021.csv"
    if raw_file.exists():
        logger.info("Found existing raw data file. Loading...")
        import pandas as pd
        try:
            df = pd.read_csv(raw_file)
            logger.info(f"Loaded {len(df)} rows from local file.")
            return df
        except Exception as e:
            logger.warning(f"Failed to load local file: {e}. Attempting download.")
    
    # Download fresh
    df = download_dataset(config)
    
    # Save to raw for future use
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_file, index=False)
    logger.info(f"Saved raw data to {raw_file}")
    
    return df

def main():
    """Entry point for ingestion script."""
    logger.info("Running data ingestion...")
    try:
        df = load_cyber_data()
        logger.info(f"Ingestion successful. Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()
