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
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Project root relative to this script's location
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_FILE = PROJECT_ROOT / "data" / ".checksums"

# Verified sources list as per task requirements
VERIFIED_SOURCES = ["zreward/zreward-v1", "zreward/zreward"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def save_checksum(file_path: Path, checksum: str) -> None:
    """Append filename and checksum to the checksums file."""
    with open(CHECKSUMS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([file_path.name, checksum])
    logger.info(f"Saved checksum for {file_path.name}: {checksum}")


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    if not CHECKSUMS_FILE.exists():
        return False
    
    with open(CHECKSUMS_FILE, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2 and row[0] == file_path.name:
                return row[1] == expected_checksum
    return False


def download_dataset() -> Path:
    """
    Attempt to fetch the Z-Reward dataset from verified sources.
    Falls back to local cache if available.
    Raises RuntimeError if all attempts fail.
    """
    output_path = DATA_RAW_DIR / "zreward_dataset.parquet"
    
    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for local cached copy first
    if output_path.exists():
        logger.info(f"Found local cached copy at {output_path}")
        # Verify checksum if available
        if CHECKSUMS_FILE.exists():
            current_checksum = calculate_sha256(output_path)
            if verify_checksum(output_path, current_checksum):
                logger.info("Checksum verification passed for cached file")
                return output_path
            else:
                logger.warning("Cached file checksum mismatch, attempting re-download")
        else:
            logger.warning("No checksum found for cached file, attempting re-download")
    
    # Attempt to load from verified sources
    for source in VERIFIED_SOURCES:
        try:
            logger.info(f"Attempting to load dataset from: {source}")
            dataset = load_dataset(source, split="train")
            
            # Save to parquet
            logger.info(f"Successfully loaded {len(dataset)} samples from {source}")
            logger.info(f"Saving to {output_path}")
            dataset.to_parquet(str(output_path))
            
            # Calculate and save checksum
            checksum = calculate_sha256(output_path)
            save_checksum(output_path, checksum)
            
            logger.info(f"Dataset successfully downloaded and saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.warning(f"Failed to load from {source}: {str(e)}")
            continue
    
    # All sources failed
    raise RuntimeError(
        f"Failed to download Z-Reward dataset from any verified source: {VERIFIED_SOURCES}. "
        f"No valid local cache found at {output_path}. "
        "Please ensure the 'datasets' package is installed and network access is available."
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_RAW_DIR),
        help="Output directory for the dataset",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        output_path = download_dataset()
        logger.info(f"Task completed successfully. Dataset saved to: {output_path}")
        return 0
    except RuntimeError as e:
        logger.error(f"Task failed: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
