"""
code/01_download_and_score.py

Task T015: Fetch HCI_P2 dataset from Hugging Face, verify required fields,
and save raw data with checksums.

This script downloads the HCI_P2 dataset, validates the presence of
'quality_rating', 'user_id', and 'dialogue_id', and stores the raw data
in data/raw/hci_p2/ along with integrity checksums.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

# Import project utilities
from utils.data_integrity import compute_file_checksum, generate_manifest
from utils.schema_validator import load_schema, validate_dataset_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/download_and_score.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "HCI_P2"
DATASET_ID = "HCI_P2/HCI_P2"  # Adjust if the actual ID differs on HF Hub
REQUIRED_FIELDS = ['quality_rating', 'user_id', 'dialogue_id']
OUTPUT_DIR = Path("data/raw/hci_p2")
CHECKSUM_FILE = OUTPUT_DIR / "checksums.json"
MANIFEST_FILE = OUTPUT_DIR / "manifest.json"

def ensure_directories():
    """Create necessary output directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "temp").mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {OUTPUT_DIR}")

def load_dataset_with_check(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """
    Load the dataset from Hugging Face Hub.

    Args:
        dataset_id: The HF Hub dataset ID.
        split: The split to load (default: 'train').

    Returns:
        A pandas DataFrame containing the dataset.

    Raises:
        RuntimeError: If the dataset cannot be loaded.
    """
    logger.info(f"Attempting to load dataset: {dataset_id}, split: {split}")
    try:
        ds = load_dataset(dataset_id, split=split)
        df = ds.to_pandas()
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise RuntimeError(f"Could not load dataset {dataset_id}. Ensure the ID is correct and internet is available.") from e

def validate_and_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate the presence of required fields and perform basic preprocessing.

    Args:
        df: Input DataFrame.

    Returns:
        Validated DataFrame.

    Raises:
        ValueError: If required fields are missing.
    """
    missing_fields = [field for field in REQUIRED_FIELDS if field not in df.columns]
    if missing_fields:
        error_msg = f"Dataset is missing required fields: {missing_fields}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Basic type checks if possible
    if not pd.api.types.is_numeric_dtype(df['quality_rating']):
        logger.warning(f"quality_rating column is not numeric. Type: {df['quality_rating'].dtype}")

    logger.info(f"Validation passed. Rows: {len(df)}, Columns: {list(df.columns)}")
    return df

def save_raw_data(df: pd.DataFrame, output_path: Path):
    """
    Save the DataFrame to parquet format.

    Args:
        df: DataFrame to save.
        output_path: Path to save the parquet file.
    """
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved raw data to {output_path}")

def generate_checksums_and_manifest(data_path: Path, checksums_path: Path, manifest_path: Path):
    """
    Generate checksums for the saved data and a manifest file.

    Args:
        data_path: Path to the parquet file.
        checksums_path: Path to save checksums JSON.
        manifest_path: Path to save manifest JSON.
    """
    checksum = compute_file_checksum(data_path)
    checksums_data = {
        "file": data_path.name,
        "sha256": checksum,
        "size_bytes": data_path.stat().st_size
    }
    with open(checksums_path, 'w') as f:
        json.dump(checksums_data, f, indent=2)
    logger.info(f"Generated checksums: {checksums_path}")

    manifest_data = {
        "dataset_name": DATASET_NAME,
        "source_id": DATASET_ID,
        "files": [data_path.name],
        "checksums_file": checksums_path.name,
        "row_count": len(pd.read_parquet(data_path)),
        "columns": list(pd.read_parquet(data_path).columns)
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Generated manifest: {manifest_path}")

def main():
    """Main entry point for T015."""
    logger.info("Starting Task T015: Download and Score HCI_P2")
    
    try:
        # 1. Ensure directories
        ensure_directories()

        # 2. Load dataset
        df = load_dataset_with_check(DATASET_ID)

        # 3. Validate
        df = validate_and_preprocess(df)

        # 4. Save raw data
        output_file = OUTPUT_DIR / "hci_p2_raw.parquet"
        save_raw_data(df, output_file)

        # 5. Generate checksums and manifest
        generate_checksums_and_manifest(output_file, CHECKSUM_FILE, MANIFEST_FILE)

        logger.info("Task T015 completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Task T015 failed: {e}")
        # Fail loudly as per constraints
        sys.exit(1)

if __name__ == "__main__":
    main()
