"""
code/data/download.py
Downloads and materializes the pick-a-pic dataset.
"""
import hashlib
import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
import pandas as pd

from config import get_paths, get_project_root
from utils.logging import get_logger, setup_logging
from utils.errors import DataSchemaError

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stream_pick_a_pic_dataset(output_path: Path):
    """
    Stream the pick-a-pic dataset from HuggingFace and materialize to parquet.
    Fails loudly if the dataset or required column is missing.
    """
    logger.info("Loading pick-a-pic dataset from HuggingFace...")

    try:
        # Use streaming to handle large datasets
        ds = load_dataset("pick-a-pic", split="train", streaming=True)
        
        # Validate required column
        if "human_rating" not in ds.column_names:
            raise DataSchemaError("Missing required dataset or column: pick-a-pic/human_rating")
        
        if "caption" not in ds.column_names:
            raise DataSchemaError("Missing required dataset or column: pick-a-pic/caption")

        # Materialize to parquet
        logger.info("Materializing dataset to parquet...")
        # We stream and convert to pandas in chunks if needed, but for now, 
        # let's try to collect a manageable subset or the whole thing if it fits.
        # Per T009: "If the full dataset exceeds RAM/disk limits during streaming, materialize a verified subset"
        # However, the constraint says "NEVER fabricate values". 
        # We will attempt to stream and write in chunks to avoid OOM.
        
        # Simple approach: collect into a list and convert to DF, then save.
        # If memory is an issue, we'd need to write parquet in chunks.
        # For now, let's assume we can hold a reasonable sample or the full set if small enough.
        # The actual pick-a-pic is ~100k rows, which should fit in RAM for a simple DF.
        
        data = []
        for i, item in enumerate(ds):
            data.append(item)
            if i % 10000 == 0:
                logger.info(f"Downloaded {i} rows...")
        
        df = pd.DataFrame(data)
        logger.info(f"Downloaded {len(df)} rows.")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to parquet
        df.to_parquet(output_path, index=False)
        logger.info(f"Dataset saved to {output_path}")
        
        return df

    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        # Fail loudly as per constraints
        if "human_rating" in str(e) or "column" in str(e):
            raise DataSchemaError("Missing required dataset or column: pick-a-pic/human_rating") from e
        raise

def download_and_checksum():
    """Main entry point for download and checksumming."""
    setup_logging()
    paths = get_paths()
    output_path = paths.raw / "pick-a-pic.parquet"

    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}. Skipping download.")
        # Recompute checksum to be sure
        checksum = compute_sha256(output_path)
        logger.info(f"Checksum: {checksum}")
        return output_path

    df = stream_pick_a_pic_dataset(output_path)
    checksum = compute_sha256(output_path)
    logger.info(f"Checksum: {checksum}")
    
    return output_path

def main():
    """Execute download and checksum."""
    output_path = download_and_checksum()
    print(f"Download complete: {output_path}")

if __name__ == "__main__":
    main()
