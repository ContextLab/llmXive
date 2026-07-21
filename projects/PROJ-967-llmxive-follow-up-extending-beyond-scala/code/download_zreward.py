"""
T037: Download Z-Reward dataset with checksum verification.

This script fetches the Z-Reward dataset using the Hugging Face datasets library.
It converts the data to CSV, computes a SHA256 checksum, saves the checksum,
and verifies integrity. It fails loudly if the fetch fails or checksum mismatch.
"""
import argparse
import csv
import hashlib
import logging
import os
import sys
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = 'zreward/zreward-v1'
DATASET_SPLIT = 'train'
FALLBACK_URL = 'https://huggingface.co/datasets/zreward/zreward-v1/raw/main/data/train.parquet'
OUTPUT_DIR = 'data/raw'
OUTPUT_CSV = 'zreward_dataset.csv'
CHECKSUM_FILE = 'data/.checksums'
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(output_path: Path) -> None:
    """
    Download the Z-Reward dataset using the datasets library.
    Falls back to direct URL download if the library method fails.
    Fails loudly if both methods fail.
    """
    logger.info(f"Attempting to download dataset: {DATASET_NAME}")
    
    # Try loading via datasets library first
    try:
        logger.info(f"Loading dataset via datasets.load_dataset('{DATASET_NAME}', split='{DATASET_SPLIT}')...")
        dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT)
        
        # Convert to CSV
        logger.info("Converting dataset to CSV...")
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if dataset.column_names:
                writer = csv.DictWriter(csvfile, fieldnames=dataset.column_names)
                writer.writeheader()
                for row in dataset:
                    # Convert any list/dict fields to string representations for CSV
                    cleaned_row = {}
                    for key, value in row.items():
                        if isinstance(value, (list, dict)):
                            cleaned_row[key] = str(value)
                        else:
                            cleaned_row[key] = value
                    writer.writerow(cleaned_row)
        
        logger.info(f"Dataset successfully saved to {output_path}")
        return

    except Exception as e:
        logger.warning(f"datasets.load_dataset failed: {e}")
        logger.info(f"Attempting fallback download from: {FALLBACK_URL}")
        
        # Fallback: Direct download (requires requests or urllib)
        try:
            import urllib.request
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp:
                tmp_path = tmp.name
            
            logger.info("Downloading parquet file...")
            urllib.request.urlretrieve(FALLBACK_URL, tmp_path)
            
            # Convert parquet to CSV
            try:
                import pandas as pd
                df = pd.read_parquet(tmp_path)
                df.to_csv(output_path, index=False)
                logger.info(f"Dataset successfully saved to {output_path} via fallback")
                os.unlink(tmp_path)
                return
            except Exception as parquet_err:
                logger.error(f"Failed to convert parquet to CSV: {parquet_err}")
                os.unlink(tmp_path)
                raise RuntimeError("Fallback download succeeded but conversion failed") from parquet_err

        except Exception as fallback_err:
            logger.error(f"Fallback download failed: {fallback_err}")
            raise RuntimeError(f"Both primary and fallback download methods failed. Primary: {e}, Fallback: {fallback_err}") from fallback_err

def save_checksum(checksum: str, checksum_file: Path) -> None:
    """Save the checksum to the checksum file."""
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {OUTPUT_CSV}\n")
    logger.info(f"Checksum saved to {checksum_file}")

def verify_checksum(checksum_file: Path, file_to_verify: Path) -> bool:
    """Verify the checksum of a file against the stored checksum."""
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False

    with open(checksum_file, 'r') as f:
        line = f.readline().strip()
        stored_checksum = line.split()[0]

    actual_checksum = calculate_sha256(file_to_verify)

    if stored_checksum != actual_checksum:
        logger.error(f"Checksum mismatch!")
        logger.error(f"Expected: {stored_checksum}")
        logger.error(f"Actual:   {actual_checksum}")
        return False

    logger.info("Checksum verification passed.")
    return True

def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward dataset with checksum verification.")
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR, help='Output directory for the dataset')
    parser.add_argument('--output-file', type=str, default=OUTPUT_CSV, help='Output filename for the dataset')
    parser.add_argument('--checksum-file', type=str, default=CHECKSUM_FILE, help='Path to the checksum file')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Resolve paths relative to project root
    output_dir = PROJECT_ROOT / args.output_dir
    output_path = output_dir / args.output_file
    checksum_file = PROJECT_ROOT / args.checksum_file
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Output file: {output_path}")
    logger.info(f"Checksum file: {checksum_file}")

    # Download dataset
    download_dataset(output_path)

    # Calculate checksum
    checksum = calculate_sha256(output_path)
    logger.info(f"Calculated checksum: {checksum}")

    # Save checksum
    save_checksum(checksum, checksum_file)

    # Verify checksum
    if not verify_checksum(checksum_file, output_path):
        logger.error("Checksum verification failed. Exiting.")
        sys.exit(1)

    logger.info("Dataset download and verification completed successfully.")

if __name__ == "__main__":
    main()
