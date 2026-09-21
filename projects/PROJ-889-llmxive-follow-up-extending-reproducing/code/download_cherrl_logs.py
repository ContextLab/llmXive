"""
Download CHERRL trajectory logs from the verified HuggingFace source.

This script implements the data ingestion pipeline for the llmXive project.
It connects to the CHERRL repository, discovers splits with required columns,
and saves the data to the project's raw data directory.

Features:
- Strict real-data mode (default): Fails loudly if source is unreachable.
- Local test mode (--local-test): Generates a small, deterministic synthetic
  subset for unit testing purposes only.
- Dynamic split discovery: Selects the first split containing J_biased,
  J_unbiased, and J_gold.
"""

import os
import sys
import hashlib
import shutil
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from datasets import load_dataset, Dataset

# Import project utilities and config
from config import get_project_root, DataConfig
from utils.io_utils import ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = ['J_biased', 'J_unbiased', 'J_gold', 'seed_id', 'bias_type', 'timestep']
HF_DATASET_ID = "CHERRL-repo/CHERRL-logs"  # Verified source from plan
OUTPUT_DIR_NAME = "cherrl_logs"
OUTPUT_FILENAME = "cherrl_logs.csv"


def verify_arxiv_source(source_url: str) -> bool:
    """
    Verify that the provided source URL matches the expected CHERRL repository.
    
    Args:
        source_url: The URL to verify.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    expected_patterns = [
        "CHERRL-repo",
        "huggingface.co/CHERRL-repo",
        "datasets/CHERRL-repo"
    ]
    
    if not any(pattern in source_url for pattern in expected_patterns):
        raise ValueError(
            f"Invalid source URL: {source_url}. "
            f"Expected a URL containing one of: {expected_patterns}"
        )
    return True


def download_from_huggingface(
    dataset_id: str = HF_DATASET_ID,
    output_path: Path = None
) -> Path:
    """
    Download real CHERRL logs from HuggingFace.
    
    This function:
    1. Connects to the verified HuggingFace dataset.
    2. Dynamically discovers available splits.
    3. Selects the first split containing required columns.
    4. Downloads the data.
    5. Saves it to the specified output path.
    
    Args:
        dataset_id: The HuggingFace dataset identifier.
        output_path: Path where the CSV will be saved.
        
    Returns:
        Path to the saved CSV file.
        
    Raises:
        SystemExit: If the source is unreachable or no valid split is found.
    """
    logger.info(f"Connecting to HuggingFace dataset: {dataset_id}")
    
    try:
        # Load dataset with streaming to handle large sizes
        # We use streaming to discover splits without downloading everything first
        dataset = load_dataset(dataset_id, split=None, streaming=True)
        
        # Get available splits
        if hasattr(dataset, 'keys'):
            splits = list(dataset.keys())
        else:
            # If it's a single split dataset
            splits = ['train'] if 'train' in str(dataset) else ['default']
            
        logger.info(f"Available splits: {splits}")
        
        valid_split = None
        valid_data = None
        
        # Iterate through splits to find one with required columns
        for split_name in splits:
            logger.info(f"Checking split: {split_name}")
            try:
                # Load the split (non-streaming for column inspection)
                split_dataset = load_dataset(dataset_id, split=split_name)
                
                # Check if required columns exist
                if all(col in split_dataset.column_names for col in REQUIRED_COLUMNS):
                    logger.info(f"Found valid split '{split_name}' with required columns")
                    valid_split = split_name
                    valid_data = split_dataset
                    break
                else:
                    missing = [col for col in REQUIRED_COLUMNS if col not in split_dataset.column_names]
                    logger.warning(f"Split '{split_name}' missing columns: {missing}")
                    
            except Exception as e:
                logger.warning(f"Failed to load split '{split_name}': {e}")
                continue
        
        if valid_data is None:
            logger.error(
                "ERROR: No valid split found with required columns "
                f"({REQUIRED_COLUMNS}). Source may be unreachable or malformed."
            )
            raise SystemExit(2)
        
        # Convert to pandas DataFrame
        df = valid_data.to_pandas()
        
        # Ensure output directory exists
        ensure_dir(output_path.parent)
        
        # Save to CSV
        logger.info(f"Saving {len(df)} rows to {output_path}")
        df.to_csv(output_path, index=False)
        
        # Compute and save checksum
        from utils.io_utils import compute_sha256
        checksum = compute_sha256(str(output_path))
        checksum_path = output_path.with_suffix('.sha256')
        checksum_path.write_text(checksum)
        logger.info(f"Checksum saved to {checksum_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download from HuggingFace: {e}")
        raise SystemExit(2)


def generate_synthetic_subset(seed: int = 42, num_rows: int = 100) -> pd.DataFrame:
    """
    Generate a small, deterministic synthetic subset for local testing.
    
    This is ONLY used when --local-test flag is provided.
    
    Args:
        seed: Random seed for reproducibility.
        num_rows: Number of rows to generate.
        
    Returns:
        A DataFrame with the required columns.
    """
    logger.info(f"Generating synthetic subset with {num_rows} rows (seed={seed})")
    
    import numpy as np
    np.random.seed(seed)
    
    # Generate synthetic data matching the expected schema
    data = {
        'seed_id': [f"seed_{i % 5}" for i in range(num_rows)],
        'bias_type': np.random.choice(['Lexical', 'Format', 'Tone', 'Self-praise'], num_rows),
        'timestep': list(range(num_rows)),
        'J_biased': np.random.uniform(0.5, 0.9, num_rows),
        'J_unbiased': np.random.uniform(0.5, 0.9, num_rows),
        'J_gold': np.random.uniform(0.5, 0.9, num_rows)
    }
    
    return pd.DataFrame(data)


def main():
    """
    Main entry point for the download script.
    
    Usage:
        python code/download_cherrl_logs.py              # Real data mode
        python code/download_cherrl_logs.py --local-test # Synthetic test mode
    """
    parser = argparse.ArgumentParser(
        description="Download CHERRL trajectory logs from HuggingFace."
    )
    parser.add_argument(
        '--local-test',
        action='store_true',
        help="Use synthetic data for local testing only. DO NOT use for production."
    )
    parser.add_argument(
        '--dataset-id',
        type=str,
        default=HF_DATASET_ID,
        help=f"HuggingFace dataset ID (default: {HF_DATASET_ID})"
    )
    
    args = parser.parse_args()
    
    # Get project root and output path
    project_root = get_project_root()
    output_dir = project_root / "data" / "raw" / OUTPUT_DIR_NAME
    output_path = output_dir / OUTPUT_FILENAME
    
    ensure_dir(output_dir)
    
    if args.local_test:
        logger.warning("LOCAL TEST MODE: Generating synthetic data")
        df = generate_synthetic_subset()
        df.to_csv(output_path, index=False)
        logger.info(f"Saved synthetic data to {output_path}")
        
        # Save checksum for test consistency
        from utils.io_utils import compute_sha256
        checksum = compute_sha256(str(output_path))
        checksum_path = output_path.with_suffix('.sha256')
        checksum_path.write_text(checksum)
        logger.info(f"Checksum saved to {checksum_path}")
        
        return 0
    
    # Real data mode
    logger.info("REAL DATA MODE: Fetching from HuggingFace")
    
    try:
        # Verify the source
        verify_arxiv_source(args.dataset_id)
        
        # Download the data
        saved_path = download_from_huggingface(
            dataset_id=args.dataset_id,
            output_path=output_path
        )
        
        logger.info(f"Successfully downloaded data to {saved_path}")
        return 0
        
    except SystemExit as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise SystemExit(2)


if __name__ == "__main__":
    sys.exit(main())
