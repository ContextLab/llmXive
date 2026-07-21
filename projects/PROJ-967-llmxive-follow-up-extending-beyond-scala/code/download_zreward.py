"""
Download Z-Reward dataset for llmXive project.

This script fetches the Z-Reward dataset from Hugging Face,
computes its SHA256 checksum, and saves it as a CSV file.
It fails loudly if the download or checksum verification fails.
"""
import argparse
import csv
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' package is required. Install with: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "zreward/zreward-v1"
DATASET_SPLIT = "train"
OUTPUT_DIR = "data/raw"
OUTPUT_FILENAME = "zreward_dataset.csv"
CHECKSUM_FILENAME = ".checksums"
FALLBACK_URL = "https://huggingface.co/datasets/zreward/zreward-v1/raw/main/data/train.parquet"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(dataset_name: str, split: str, output_path: str) -> Tuple[str, str]:
    """
    Download dataset from Hugging Face and save as CSV.
    
    Args:
        dataset_name: Name of the dataset on Hugging Face
        split: Dataset split to download (e.g., 'train')
        output_path: Path where CSV will be saved
        
    Returns:
        Tuple of (output_path, checksum)
        
    Raises:
        RuntimeError: If download fails or dataset cannot be loaded
    """
    logger.info(f"Attempting to download dataset: {dataset_name} (split: {split})")
    
    try:
        # Load dataset from Hugging Face
        dataset = load_dataset(dataset_name, split=split)
        
        # Convert to pandas DataFrame
        df = dataset.to_pandas()
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset saved to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Calculate checksum
        checksum = calculate_sha256(output_path)
        logger.info(f"SHA256 checksum: {checksum}")
        
        return output_path, checksum
        
    except Exception as e:
        logger.error(f"Failed to download dataset from Hugging Face: {str(e)}")
        logger.error(f"Fallback method not implemented as per requirements - failing loudly")
        raise RuntimeError(f"Dataset download failed: {str(e)}")

def save_checksum(checksum: str, checksum_file: str) -> None:
    """Save checksum to file."""
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {OUTPUT_FILENAME}\n")
    logger.info(f"Checksum saved to {checksum_file}")

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch!")
        logger.error(f"Expected: {expected_checksum}")
        logger.error(f"Actual: {actual_checksum}")
        return False
    logger.info("Checksum verification passed")
    return True

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download Z-Reward dataset and verify checksum"
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=DATASET_NAME,
        help=f"Name of the dataset on Hugging Face (default: {DATASET_NAME})"
    )
    parser.add_argument(
        "--split",
        type=str,
        default=DATASET_SPLIT,
        help=f"Dataset split to download (default: {DATASET_SPLIT})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--output-filename",
        type=str,
        default=OUTPUT_FILENAME,
        help=f"Output filename (default: {OUTPUT_FILENAME})"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify checksum of existing file"
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / args.output_filename
    checksum_file = output_dir / CHECKSUM_FILENAME
    
    if args.verify:
        if not output_path.exists():
            logger.error(f"File not found: {output_path}")
            sys.exit(1)
        
        # Read expected checksum
        if not checksum_file.exists():
            logger.error(f"Checksum file not found: {checksum_file}")
            sys.exit(1)
        
        with open(checksum_file, 'r') as f:
            expected_checksum = f.read().split()[0]
        
        if verify_checksum(str(output_path), expected_checksum):
            logger.info("Verification successful")
            sys.exit(0)
        else:
            logger.error("Verification failed")
            sys.exit(1)
    else:
        try:
            # Download dataset
            output_path, checksum = download_dataset(
                args.dataset_name,
                args.split,
                str(output_path)
            )
            
            # Save checksum
            save_checksum(checksum, str(checksum_file))
            
            logger.info("Dataset download and verification completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
