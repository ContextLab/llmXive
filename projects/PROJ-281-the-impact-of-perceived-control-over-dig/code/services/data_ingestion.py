import json
import logging
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from datasets import load_dataset

from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, CONFIG

logger = logging.getLogger(__name__)

DATASET_NAME = "cardiffnlp/tweet_sentiment_extraction"
EXPECTED_COLUMNS = ["text", "id", "label"]
CHECKSUM_FILE = DATA_RAW_DIR / "social_media.csv.checksum"

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_and_validate_dataset() -> Optional[Path]:
    """
    Downloads the dataset from HuggingFace to data/raw/social_media.csv.
    Validates the download and returns the path if successful.
    Returns None if the download fails or the dataset is empty.
    """
    output_path = DATA_RAW_DIR / "social_media.csv"
    
    # Ensure directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting download of dataset: {DATASET_NAME}")
    
    try:
        # Load dataset
        dataset = load_dataset(DATASET_NAME, split="train", trust_remote_code=True)
        
        if dataset is None or len(dataset) == 0:
            logger.error("Downloaded dataset is empty.")
            return None

        # Convert to DataFrame
        df = dataset.to_pandas()
        
        # Validate columns
        missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
        if missing_cols:
            logger.error(f"Missing expected columns in dataset: {missing_cols}")
            return None

        # Ensure 'text' column exists and is not empty
        if 'text' not in df.columns:
            logger.error("Dataset does not contain 'text' column.")
            return None
        
        # Check for empty dataframe after loading
        if df.empty:
            logger.error("Dataset is empty after conversion to DataFrame.")
            return None

        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset saved to {output_path} with {len(df)} rows.")

        # Calculate and save checksum
        checksum = _calculate_sha256(output_path)
        with open(CHECKSUM_FILE, "w") as f:
            json.dump({"checksum": checksum, "rows": len(df)}, f)
        
        logger.info(f"Checksum calculated and saved: {checksum}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}", exc_info=True)
        return None

def validate_existing_dataset() -> Optional[Path]:
    """
    Validates an existing dataset file if it exists.
    Returns the path if valid, None otherwise.
    """
    output_path = DATA_RAW_DIR / "social_media.csv"
    
    if not output_path.exists():
        logger.info("Existing dataset not found.")
        return None

    try:
        # Check checksum if available
        if CHECKSUM_FILE.exists():
            with open(CHECKSUM_FILE, "r") as f:
                saved_data = json.load(f)
            current_checksum = _calculate_sha256(output_path)
            if current_checksum != saved_data.get("checksum"):
                logger.warning("Checksum mismatch. Dataset may be corrupted.")
                return None
            logger.info("Existing dataset validated via checksum.")
        else:
            logger.warning("Checksum file not found. Validating row count only.")
            df = pd.read_csv(output_path)
            if df.empty:
                logger.error("Existing dataset is empty.")
                return None
            logger.info(f"Existing dataset validated with {len(df)} rows.")
        
        return output_path
    except Exception as e:
        logger.error(f"Failed to validate existing dataset: {e}", exc_info=True)
        return None

def run_data_ingestion_pipeline() -> Optional[Path]:
    """
    Main entry point for the data ingestion pipeline.
    Tries to validate existing data first, then downloads if necessary.
    Returns the path to the downloaded/validated dataset or None on failure.
    """
    logger.info("Starting data ingestion pipeline.")
    
    # Try to validate existing data
    existing_path = validate_existing_dataset()
    if existing_path:
        return existing_path

    # If no valid existing data, download
    logger.info("No valid existing dataset found. Downloading...")
    return download_and_validate_dataset()