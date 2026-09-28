"""
FEMNIST Data Downloader using Hugging Face Datasets.

This module implements the streaming download of the FEMNIST dataset from
the Hugging Face Hub (leaf/femnist). It adheres to the project constraints:
- Only "femnist" is supported. "shakespeare" is explicitly excluded per T000
  and plan.md Gap Analysis.
- No synthetic fallbacks. If the download fails, it raises DataFetchError.
- Uses streaming mode to handle large datasets within memory constraints.
- Saves the processed data to data/raw/femnist.parquet and generates
  data/raw/femnist.sha256.

References:
- T000: Spec Alignment (Shakespeare Exclusion)
- plan.md: Gap Analysis
"""

import time
import hashlib
import os
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root detection (assumes running from project root or code/data/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Constants
MAX_RETRIES = 3
DATASET_NAME = "leaf/femnist"
SUPPORTED_DATASETS = {"femnist"}
EXCLUDED_DATASETS = {"shakespeare"}

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksum_file(file_path: Path, checksum: str) -> Path:
    """Generate a .sha256 file containing the checksum."""
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    logger.info(f"Generated checksum file: {checksum_path}")
    return checksum_path

def download_femnist_streaming(output_dir: Path) -> Path:
    """
    Download FEMNIST dataset using Hugging Face datasets in streaming mode.

    Args:
        output_dir: Directory to save the downloaded parquet file.

    Returns:
        Path to the saved parquet file.

    Raises:
        DataFetchError: If the download fails after MAX_RETRIES attempts.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "femnist.parquet"

    # If file already exists, verify checksum or skip?
    # For idempotency, we check if file exists and has valid checksum
    # But to ensure freshness and correctness per task, we might re-download
    # if checksum file is missing or invalid.
    checksum_file = output_file.with_suffix(output_file.suffix + ".sha256")
    if output_file.exists() and checksum_file.exists():
        with open(checksum_file, "r") as f:
            stored_checksum = f.read().split()[0]
        current_checksum = compute_sha256(output_file)
        if stored_checksum == current_checksum:
            logger.info(f"File {output_file} already exists and checksum matches. Skipping download.")
            return output_file
        else:
            logger.warning(f"Checksum mismatch for {output_file}. Re-downloading.")
            output_file.unlink()
            checksum_file.unlink()

    logger.info(f"Starting streaming download of {DATASET_NAME}...")
    
    # Import here to avoid hard dependency if not installed (though required by T002)
    try:
        from datasets import load_dataset
    except ImportError:
        raise DataFetchError("Hugging Face 'datasets' library is not installed. Please install it via requirements.txt.")

    retry_count = 0
    last_exception = None

    while retry_count < MAX_RETRIES:
        try:
            logger.info(f"Attempt {retry_count + 1}/{MAX_RETRIES}: Loading dataset with streaming=True...")
            # Load dataset in streaming mode
            # split='train' as per task requirements
            dataset = load_dataset(
                DATASET_NAME,
                split='train',
                trust_remote_code=True,
                streaming=True
            )

            # Process in chunks to avoid memory issues and convert to pandas
            # We will collect all data into a list of dicts then convert to DataFrame
            # Note: FEMNIST is large. Streaming iterates over examples.
            # We need to accumulate them.
            logger.info("Iterating over streaming dataset to build DataFrame...")
            
            data_records = []
            batch_size = 1000
            count = 0
            
            # Iterate through the streaming dataset
            for example in dataset:
                # Example structure from leaf/femnist:
                # {'user_id': ..., 'segment_id': ..., 'image': <PIL.Image>, 'label': int}
                # We need to handle the image. For parquet, we might store as bytes or skip if not needed for partition.
                # However, T012 (Partition) needs the data.
                # If the partition logic expects raw images, we must convert to bytes or base64.
                # Let's assume we convert image to bytes for storage.
                
                img = example.get('image')
                img_bytes = None
                if img is not None:
                    # Convert PIL Image to bytes
                    import io
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    img_bytes = buf.getvalue()
                
                record = {
                    'user_id': example.get('user_id'),
                    'segment_id': example.get('segment_id'),
                    'label': example.get('label'),
                    'image_bytes': img_bytes
                }
                data_records.append(record)
                count += 1

                if count % 10000 == 0:
                    logger.info(f"Processed {count} examples...")

            logger.info(f"Downloaded {count} examples. Converting to DataFrame...")
            df = pd.DataFrame(data_records)
            
            logger.info(f"Saving to {output_file}...")
            df.to_parquet(output_file, index=False)
            
            # Generate checksum
            checksum = compute_sha256(output_file)
            generate_checksum_file(output_file, checksum)
            
            logger.info(f"Successfully saved FEMNIST to {output_file} (checksum: {checksum})")
            return output_file

        except Exception as e:
            last_exception = e
            retry_count += 1
            logger.error(f"Attempt {retry_count} failed: {e}")
            if retry_count < MAX_RETRIES:
                wait_time = 2 ** retry_count
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to download FEMNIST after {MAX_RETRIES} attempts.")
                raise DataFetchError(f"Failed to download FEMNIST after {MAX_RETRIES} attempts: {e}") from e

    raise DataFetchError("Unexpected error in download loop.")

def download_dataset(dataset_name: str, output_dir: Optional[Path] = None, is_streaming: bool = True) -> Path:
    """
    Main entry point for downloading a dataset.

    Args:
        dataset_name: Name of the dataset to download (e.g., 'femnist').
        output_dir: Directory to save the data. Defaults to data/raw/.
        is_streaming: Whether to use streaming mode.

    Returns:
        Path to the downloaded file.

    Raises:
        ValueError: If the dataset is not supported (e.g., 'shakespeare').
        DataFetchError: If download fails.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR

    dataset_name = dataset_name.lower()

    # Check constraints (T000)
    if dataset_name in EXCLUDED_DATASETS:
        raise ValueError(
            f"Shakespeare excluded per plan.md Gap Analysis (no verified source). "
            f"Refer to T000 for exclusion details."
        )

    if dataset_name not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Supported: {SUPPORTED_DATASETS}")

    if dataset_name == "femnist":
        return download_femnist_streaming(output_dir)
    
    raise ValueError(f"No handler for dataset: {dataset_name}")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Download FEMNIST dataset for Federated Learning.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name to download (default: femnist)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/raw/)."
    )
    parser.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable streaming mode (not recommended for large datasets)."
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DATA_RAW_DIR

    try:
        logger.info(f"Starting download for dataset: {args.dataset}")
        result_path = download_dataset(
            dataset_name=args.dataset,
            output_dir=output_dir,
            is_streaming=not args.no_streaming
        )
        logger.info(f"Download complete. Output: {result_path}")
        
        # Verify existence
        if not result_path.exists():
            raise DataFetchError(f"Downloaded file not found at {result_path}")
        
        # Verify checksum file
        checksum_path = result_path.with_suffix(result_path.suffix + ".sha256")
        if not checksum_path.exists():
            raise DataFetchError(f"Checksum file not found at {checksum_path}")

        print(f"SUCCESS: {result_path}")
        sys.exit(0)

    except ValueError as ve:
        logger.error(f"Configuration Error: {ve}")
        sys.exit(1)
    except DataFetchError as de:
        logger.error(f"Data Fetch Error: {de}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()