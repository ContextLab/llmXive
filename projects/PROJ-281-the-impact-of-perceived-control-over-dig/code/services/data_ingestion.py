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

class DataFetchError(Exception):
    """Raised when a real data fetch fails, preventing fallback to synthetic data."""
    pass

def _calculate_sha256_streaming(dataset, chunk_size: int = 10000) -> str:
    """
    Calculate a running SHA256 hash over dataset rows in chunks.
    This avoids loading the full dataset into memory for the hash calculation.
    """
    sha256_hash = hashlib.sha256()
    rows_processed = 0
    
    # We need to serialize the data in a deterministic way to match the CSV content
    # We'll iterate through the dataset and hash the string representation of each row
    # in the same order they would appear in the CSV.
    
    logger.info("Starting streaming hash calculation...")
    
    for i in range(0, len(dataset), chunk_size):
        chunk = dataset.select(range(i, min(i + chunk_size, len(dataset))))
        chunk_str = ""
        for row in chunk:
            # Ensure deterministic string representation
            # Sort keys to ensure consistent order
            row_str = json.dumps(row, sort_keys=True)
            chunk_str += row_str + "\n"
        
        sha256_hash.update(chunk_str.encode('utf-8'))
        rows_processed += len(chunk)
        if rows_processed % 100000 == 0:
            logger.info(f"Processed {rows_processed} rows for hash...")
    
    logger.info(f"Hash calculation complete for {rows_processed} rows.")
    return sha256_hash.hexdigest()

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_and_validate_dataset(use_streaming: bool = True) -> Optional[Path]:
    """
    Downloads the dataset from HuggingFace to data/raw/social_media.csv.
    Supports streaming mode for large datasets to avoid OOM.
    Validates the download and returns the path if successful.
    Raises DataFetchError if the download fails or the dataset is empty.
    
    Args:
        use_streaming (bool): If True, uses streaming=True to load dataset in chunks.
                              If False, loads the full dataset into memory.
    """
    output_path = DATA_RAW_DIR / "social_media.csv"
    
    # Ensure directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting download of dataset: {DATASET_NAME} (streaming={use_streaming})")
    
    try:
        # Load dataset with streaming option
        if use_streaming:
            logger.info("Loading dataset in streaming mode...")
            dataset = load_dataset(DATASET_NAME, split="train", trust_remote_code=True, streaming=True)
            # Convert streaming dataset to list to get length and iterate
            # Note: For very large datasets, we might want to process in chunks directly
            # but for simplicity and checksum consistency, we'll materialize it in chunks
            # and write to CSV incrementally.
            
            # First, let's get the dataset as a list for now (this might still be large)
            # A better approach for truly huge datasets would be to stream directly to CSV
            # but we need to be careful about memory.
            # For this implementation, we'll use streaming to avoid initial OOM on load,
            # then write to CSV in chunks.
            
            # Convert to a list of dicts for CSV writing
            # This is memory intensive for huge datasets, so we'll do it in batches
            df_chunks = []
            batch_size = 50000
            current_chunk = []
            
            logger.info("Processing dataset in chunks for CSV writing...")
            for i, row in enumerate(dataset):
                current_chunk.append(row)
                if len(current_chunk) >= batch_size:
                    chunk_df = pd.DataFrame(current_chunk)
                    df_chunks.append(chunk_df)
                    current_chunk = []
                    logger.info(f"Processed {i+1} rows...")
            
            # Add remaining rows
            if current_chunk:
                df_chunks.append(pd.DataFrame(current_chunk))
            
            if not df_chunks:
                logger.error("Dataset is empty after streaming load.")
                raise DataFetchError("Dataset is empty after streaming load.")
            
            # Concatenate chunks and save
            logger.info("Concatenating chunks and saving to CSV...")
            full_df = pd.concat(df_chunks, ignore_index=True)
            
            # Validate columns
            missing_cols = set(EXPECTED_COLUMNS) - set(full_df.columns)
            if missing_cols:
                logger.error(f"Missing expected columns in dataset: {missing_cols}")
                raise DataFetchError(f"Missing expected columns: {missing_cols}")

            # Ensure 'text' column exists and is not empty
            if 'text' not in full_df.columns:
                logger.error("Dataset does not contain 'text' column.")
                raise DataFetchError("Dataset does not contain 'text' column.")
            
            # Check for empty dataframe after loading
            if full_df.empty:
                logger.error("Dataset is empty after conversion to DataFrame.")
                raise DataFetchError("Dataset is empty after conversion to DataFrame.")

            # Save to CSV
            full_df.to_csv(output_path, index=False)
            row_count = len(full_df)
            logger.info(f"Dataset saved to {output_path} with {row_count} rows.")

            # Calculate checksum from the saved file
            checksum = _calculate_sha256(output_path)
            
        else:
            # Non-streaming mode (original behavior)
            dataset = load_dataset(DATASET_NAME, split="train", trust_remote_code=True)
            
            if dataset is None or len(dataset) == 0:
                logger.error("Downloaded dataset is empty.")
                raise DataFetchError("Downloaded dataset is empty.")

            # Convert to DataFrame
            df = dataset.to_pandas()
            
            # Validate columns
            missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
            if missing_cols:
                logger.error(f"Missing expected columns in dataset: {missing_cols}")
                raise DataFetchError(f"Missing expected columns: {missing_cols}")

            # Ensure 'text' column exists and is not empty
            if 'text' not in df.columns:
                logger.error("Dataset does not contain 'text' column.")
                raise DataFetchError("Dataset does not contain 'text' column.")
            
            # Check for empty dataframe after loading
            if df.empty:
                logger.error("Dataset is empty after conversion to DataFrame.")
                raise DataFetchError("Dataset is empty after conversion to DataFrame.")

            # Save to CSV
            df.to_csv(output_path, index=False)
            row_count = len(df)
            logger.info(f"Dataset saved to {output_path} with {row_count} rows.")

            # Calculate and save checksum
            checksum = _calculate_sha256(output_path)

        # Save checksum and metadata
        with open(CHECKSUM_FILE, "w") as f:
            json.dump({
                "checksum": checksum, 
                "rows": row_count,
                "streaming_used": use_streaming
            }, f)
        
        logger.info(f"Checksum calculated and saved: {checksum}")
        return output_path

    except DataFetchError:
        # Re-raise our specific error immediately
        raise
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}", exc_info=True)
        raise DataFetchError(f"Real data fetch failed: {e}")

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

def run_data_ingestion_pipeline(use_streaming: bool = True) -> Optional[Path]:
    """
    Main entry point for the data ingestion pipeline.
    Tries to validate existing data first, then downloads if necessary.
    Supports streaming mode for large datasets.
    
    Args:
        use_streaming (bool): If True, uses streaming mode for dataset loading.
                              Defaults to True as per T048 requirements.
    
    Returns:
        Optional[Path]: Path to the downloaded/validated dataset or None on failure.
    """
    logger.info(f"Starting data ingestion pipeline (streaming={use_streaming}).")
    
    # Try to validate existing data
    existing_path = validate_existing_dataset()
    if existing_path:
        return existing_path

    # If no valid existing data, download with streaming
    logger.info("No valid existing dataset found. Downloading with streaming...")
    return download_and_validate_dataset(use_streaming=use_streaming)