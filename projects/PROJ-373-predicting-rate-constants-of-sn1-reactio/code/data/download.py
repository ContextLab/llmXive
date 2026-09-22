import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Optional

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
STREAMING_THRESHOLD_GB = 7.0
STREAMING_THRESHOLD_BYTES = STREAMING_THRESHOLD_GB * (1024 ** 3)
MAX_RETRIES = 5
BASE_DELAY = 1.0  # seconds

# Verified dataset sources per task spec
DATASET_IDS = [
    "author/DTS-SN1-15-01-2024",
    "author/SN18-All-20240204"
]

def check_schema_pass(schema_log_path: str) -> bool:
    """Check if schema check passed by reading the log file."""
    if not os.path.exists(schema_log_path):
        logger.error(f"Schema check log not found at {schema_log_path}")
        return False
    
    try:
        with open(schema_log_path, 'r') as f:
            content = f.read()
            # Strict check for pass status
            return 'status: \'pass\'' in content or 'status: "pass"' in content
    except Exception as e:
        logger.error(f"Error reading schema log: {e}")
        return False

def get_dataset_size(dataset_name: str) -> int:
    """
    Estimate dataset size by checking file info from HuggingFace.
    Returns size in bytes.
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        # Try to get repo info
        info = api.repo_info(dataset_name, repo_type="dataset")
        total_size = 0
        for file_info in info.siblings:
            if file_info.size:
                total_size += file_info.size
        return total_size
    except Exception as e:
        logger.warning(f"Could not determine dataset size for {dataset_name}: {e}. Defaulting to streaming.")
        return STREAMING_THRESHOLD_BYTES + 1  # Force streaming if unknown

def download_dataset(dataset_name: str, output_path: str):
    """
    Download dataset from HuggingFace.
    Uses streaming if estimated size > 7GB, otherwise loads directly.
    """
    try:
        from datasets import load_dataset
        import pandas as pd
        
        # Determine if we need streaming
        estimated_size = get_dataset_size(dataset_name)
        use_streaming = estimated_size > STREAMING_THRESHOLD_BYTES
        
        logger.info(f"Dataset {dataset_name} estimated size: {estimated_size / (1024**3):.2f} GB. "
                    f"Using streaming: {use_streaming}")
        
        if use_streaming:
            # Load with streaming to avoid memory issues
            logger.info("Loading dataset with streaming=True...")
            dataset = load_dataset(dataset_name, split='train', streaming=True)
            
            # Convert to dataframe by iterating
            # Note: streaming datasets are iterators, we need to materialize
            data_list = []
            for idx, item in enumerate(dataset):
                data_list.append(item)
                if idx % 10000 == 0:
                    logger.info(f"Downloaded {idx} rows...")
            
            df = pd.DataFrame(data_list)
            logger.info(f"Materialized {len(df)} rows from streaming dataset.")
        else:
            # Load directly into memory
            logger.info("Loading dataset into memory...")
            dataset = load_dataset(dataset_name, split='train')
            df = dataset.to_pandas()
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save to parquet
        logger.info(f"Saving dataset to {output_path}...")
        df.to_parquet(output_path, index=False)
        logger.info(f"Dataset saved successfully. Total rows: {len(df)}")
        
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {e}")
        return False, str(e)

def download_with_retry(dataset_name: str, output_path: str, max_retries: int = MAX_RETRIES):
    """
    Attempt to download dataset with exponential backoff retry logic.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Download attempt {attempt + 1}/{max_retries}")
            success, error = download_dataset(dataset_name, output_path)
            if success:
                return True, None
            
            # If it's a network error, retry
            if "network" in error.lower() or "timeout" in error.lower() or "connection" in error.lower():
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning(f"Network error, retrying in {delay}s: {error}")
                time.sleep(delay)
                continue
            else:
                # Non-retryable error
                return False, error
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed with exception: {e}")
            if attempt == max_retries - 1:
                return False, str(e)
            delay = BASE_DELAY * (2 ** attempt)
            time.sleep(delay)
    
    return False, f"Failed after {max_retries} attempts"

def main():
    parser = argparse.ArgumentParser(description="Download SN1 dataset")
    parser.add_argument("--dataset", type=str, 
                      default=DATASET_IDS[0], 
                      help=f"HuggingFace dataset name (default: {DATASET_IDS[0]})")
    parser.add_argument("--output", type=str, 
                      default="data/raw/sn1_raw.parquet", 
                      help="Output file path")
    parser.add_argument("--schema-log", type=str, 
                      default="data/processed/schema_check.log", 
                      help="Schema check log path")
    args = parser.parse_args()

    # Ensure directories exist
    ensure_dirs()
    
    # Check schema first (T011a dependency)
    logger.info("Checking schema validation status...")
    if not check_schema_pass(args.schema_log):
        logger.error("Schema check failed or not found. Aborting download as per T011a dependency.")
        logger.error("Please ensure T011a (schema_check.py) has run successfully and produced data/processed/schema_check.log")
        sys.exit(1)
    
    logger.info(f"Schema check passed. Proceeding to download {args.dataset}...")
    
    # Download with retry logic
    success, error = download_with_retry(args.dataset, args.output)
    
    if not success:
        logger.error(f"Download failed after retries: {error}")
        sys.exit(1)
    
    logger.info("Download completed successfully")
    logger.info(f"Output file: {args.output}")

if __name__ == "__main__":
    main()