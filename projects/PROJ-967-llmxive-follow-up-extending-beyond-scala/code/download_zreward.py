import argparse
import csv
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import datasets; if missing, raise a clear error rather than using synthetic data
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required for T037. "
        "Install it via: pip install datasets"
    )

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = RAW_DATA_DIR / "z_reward_data.parquet"
CHECKSUM_FILE = RAW_DATA_DIR / "z_reward_data.sha256"

# Expected schema columns (logical names mapped to potential dataset keys)
REQUIRED_COLUMNS = {
    "prompt",
    "image_url",
    "teacher_scores",  # Expected to be a dict or struct
    "student_scalar",
    "human_annotations",  # Expected to be a dict or struct
    "primary_dimension"
}

# Verified sources prioritized list
# 1. Primary: Hugging Face Dataset (Z-Reward Evaluation)
# Note: We try the most likely candidate first. If the exact name differs,
# the code below attempts to fetch and validate.
DATASET_SOURCES = [
    "z-reward/z-reward",
    # Fallback candidates if the primary name is incorrect (hypothetical)
    # "z-reward/evaluation",
    # "z-reward/zreward"
]

def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def save_checksum(file_path: Path, checksum: str) -> None:
    with open(CHECKSUM_FILE, "w") as f:
        f.write(checksum)

def verify_checksum(file_path: Path) -> bool:
    if not CHECKSUM_FILE.exists():
        return False
    stored_checksum = CHECKSUM_FILE.read_text().strip()
    current_checksum = calculate_sha256(file_path)
    return stored_checksum == current_checksum

def validate_columns(df) -> None:
    """
    Validates that the loaded dataset contains the required logical columns.
    Raises RuntimeError if critical columns are missing.
    """
    # Check for top-level string columns
    missing_top_level = []
    for col in REQUIRED_COLUMNS:
        if col not in df.column_names:
            # Check for common variations if exact match fails
            found = False
            for actual_col in df.column_names:
                if actual_col.lower() == col.lower():
                    found = True
                    break
            if not found:
                missing_top_level.append(col)

    if missing_top_level:
        raise RuntimeError(
            f"Dataset is missing required top-level columns: {missing_top_level}. "
            f"Available columns: {df.column_names}. "
            "This dataset does not match the expected Z-Reward schema."
        )

    # Specific validation for dictionary/struct columns if present
    # We assume 'teacher_scores' and 'human_annotations' are dicts or structs.
    # If they are missing, we already caught them above.
    # If they exist, we verify they aren't empty or malformed in a basic way.
    # For now, presence is the primary check as per task description.

def download_dataset(logger: logging.Logger) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # If file already exists and checksum matches, skip download
    if OUTPUT_FILE.exists() and verify_checksum(OUTPUT_FILE):
        logger.info(f"Dataset already exists and checksum verified: {OUTPUT_FILE}")
        return OUTPUT_FILE

    logger.info("Attempting to fetch Z-Reward evaluation dataset...")
    dataset = None

    for source in DATASET_SOURCES:
        try:
            logger.info(f"Trying source: {source}")
            # Attempt to load the dataset
            # streaming=False to ensure we get the full structure for validation
            # Use trust_remote_code=True if necessary, though standard HF datasets usually don't need it
            dataset = load_dataset(source, split="train")
            
            # Validate schema immediately
            validate_columns(dataset)
            
            logger.info(f"Successfully loaded and validated dataset from {source}")
            break
        except Exception as e:
            logger.warning(f"Failed to load from {source}: {e}")
            continue

    if dataset is None:
        raise RuntimeError(
            "Failed to download Z-Reward dataset from any verified source. "
            "No valid data source found. Please check the dataset availability on Hugging Face Hub."
        )

    # Convert to Parquet to ensure efficient storage and schema preservation
    # The 'datasets' library supports direct to_parquet
    logger.info(f"Saving dataset to {OUTPUT_FILE}")
    dataset.to_parquet(str(OUTPUT_FILE))

    # Calculate and save checksum
    checksum = calculate_sha256(OUTPUT_FILE)
    save_checksum(OUTPUT_FILE, checksum)
    logger.info(f"Saved checksum: {checksum}")

    return OUTPUT_FILE

def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward Evaluation Dataset")
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="Path to save the downloaded dataset (default: data/raw/z_reward_data.parquet)"
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()
    
    # Override output path if provided
    global OUTPUT_FILE
    OUTPUT_FILE = Path(args.output)
    # Update checksum file path relative to new output
    global CHECKSUM_FILE
    CHECKSUM_FILE = OUTPUT_FILE.with_suffix('.sha256')

    try:
        result_path = download_dataset(logger)
        logger.info(f"Task T037 completed successfully. Data saved to: {result_path}")
        return 0
    except Exception as e:
        logger.error(f"Task T037 failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())