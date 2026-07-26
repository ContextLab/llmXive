import argparse
import csv
import hashlib
import logging
import os
import sys
from pathlib import Path
import time

# Attempt to import datasets; if missing, we will let the import error surface
try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package is required. Install via: pip install datasets")
    sys.exit(1)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum, filepath, checksum_file):
    """Save checksum to a file."""
    with open(checksum_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([os.path.basename(filepath), checksum])
    logging.info(f"Checksum saved to {checksum_file}")

def verify_checksum(filepath, checksum_file):
    """Verify file checksum against stored value."""
    if not os.path.exists(checksum_file):
        return False, "Checksum file not found"

    with open(checksum_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0] == os.path.basename(filepath):
                stored_checksum = row[1]
                current_checksum = calculate_sha256(filepath)
                if current_checksum == stored_checksum:
                    return True, "Checksum verified"
                else:
                    return False, f"Checksum mismatch: expected {stored_checksum}, got {current_checksum}"
    return False, "Checksum entry not found"

def download_dataset(logger):
    """
    Attempt to fetch the Z-Reward evaluation dataset.
    Prioritized sources:
    1. Z-Reward/eval-dataset
    2. UCI/imagenet-rewards
    Falls back to local cache if available, then raises RuntimeError.
    """
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "imagenet_rewards.parquet"
    checksum_file = output_dir.parent / ".checksums"

    # If file already exists and checksum matches, skip download
    if output_file.exists():
        valid, msg = verify_checksum(str(output_file), str(checksum_file))
        if valid:
            logger.info(f"Dataset already exists and checksum verified: {output_file}")
            return str(output_file)
        else:
            logger.warning(f"Existing file checksum invalid or missing: {msg}. Re-downloading...")
            os.remove(output_file)

    sources = ['Z-Reward/eval-dataset', 'UCI/imagenet-rewards']
    dataset = None
    last_error = None

    for source in sources:
        logger.info(f"Attempting to load dataset from: {source}")
        try:
            # Try loading with streaming first to check availability without full download
            # Then load full dataset if streaming works
            ds_stream = load_dataset(source, split="train", streaming=True)
            # If streaming works, load full dataset
            # Note: We use streaming=False for the actual load to get a parquet-compatible object
            # But we rely on the stream check to verify existence first.
            # However, load_dataset with streaming=True returns an IterableDataset which is not easily saved to parquet.
            # So we load normally. If it's too big, the task requires chunked loading later, but here we just fetch.
            # For the initial download task, we attempt a standard load.
            # If the dataset is huge, we might need to handle it, but the task says "Download".
            # We'll try loading the full dataset. If it fails due to size, we might need to adjust,
            # but the primary goal is to get the real data file.
            # To be safe with memory, we will try to load a subset if the full load fails,
            # BUT the constraint says "NO synthetic fallbacks". If we can't get the full data, we fail.
            # However, the task says "Save the raw data". If the dataset is 7GB+, we might need to stream and save chunks.
            # Let's try to load the full dataset first.
            dataset = load_dataset(source, split="train")
            logger.info(f"Successfully loaded dataset from {source}")
            break
        except Exception as e:
            last_error = e
            logger.warning(f"Failed to load from {source}: {e}")
            continue

    if dataset is None:
        error_msg = (
            f"Failed to download dataset from all sources: {sources}. "
            f"Last error: {last_error}. "
            f"Please check network connectivity or dataset availability."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Save to parquet
    logger.info(f"Saving dataset to {output_file}")
    try:
        dataset.to_parquet(str(output_file))
    except Exception as e:
        logger.error(f"Failed to save dataset to parquet: {e}")
        raise RuntimeError(f"Failed to save dataset: {e}")

    # Calculate and save checksum
    checksum = calculate_sha256(str(output_file))
    save_checksum(checksum, str(output_file), str(checksum_file))
    logger.info(f"Dataset downloaded and saved: {output_file} (SHA256: {checksum})")

    return str(output_file)

def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward evaluation dataset")
    parser.add_argument("--output", type=str, default="data/raw/imagenet_rewards.parquet",
                        help="Path to save the downloaded dataset")
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    try:
        output_path = download_dataset(logger)
        logger.info(f"Task T037 completed successfully. Data saved at: {output_path}")
    except RuntimeError as e:
        logger.error(f"Task T037 failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
