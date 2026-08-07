import os
import sys
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

from datasets import load_dataset
from src.config import setup_logging

# Ensure logging is configured before use
logger = setup_logging(__name__)

# Constants for data paths
DATA_RAW_DIR = Path("data/raw")
DATA_ARCHIVE_DIR = DATA_RAW_DIR / "archive"
DATA_PROVENANCE_DIR = Path("data/provenance")
STATE_DIR = Path("state/projects")

# Dataset identifiers
FULL_EBD_DATASET_ID = "ebird/ebd-full"  # Hypothetical verified ID if available
SAMPLE_DATASET_ID = "vvud/eb-data"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise

def check_real_data_available(dataset_id: str) -> bool:
    """
    Verify if a real dataset is available on HuggingFace.
    This function attempts to list the dataset to confirm existence.
    """
    try:
        logger.info(f"Checking availability of dataset: {dataset_id}")
        # Attempt to load metadata only to verify existence without downloading full data
        ds = load_dataset(dataset_id, split="train", streaming=True)
        # If we can get an iterator, it exists
        next(iter(ds))
        logger.info(f"Dataset {dataset_id} is available.")
        return True
    except Exception as e:
        logger.warning(f"Dataset {dataset_id} not available or inaccessible: {e}")
        return False

def download_and_verify_data(
    dataset_id: str,
    output_dir: Path,
    expected_checksum: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download dataset from HuggingFace and verify checksums.
    Returns metadata about the download.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Starting download of {dataset_id} to {output_dir}")

    try:
        # Load dataset with streaming=False to download to cache then copy
        # We use streaming=True to avoid OOM, but for the specific task of
        # "downloading and verifying", we need the physical files.
        # Since HuggingFace datasets are often cached, we can try to save them.
        # However, for large datasets, we might need to process chunks.
        # For this task, we assume the dataset is small enough or we download a subset
        # if it's the sample dataset.
        
        # If it's the sample dataset, we might download the whole thing.
        # If it's the full EBD, we might need to stream and save chunks.
        
        # Strategy: Use load_dataset with streaming=True, iterate and save to parquet/arrow
        # This satisfies "download" by persisting the data to disk.
        
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Save to a temporary parquet file in the output directory
        # We will iterate through the dataset and save it in chunks
        output_file = output_dir / "ebird_data.parquet"
        
        # If the file already exists and checksum matches, skip download
        if output_file.exists():
            current_checksum = compute_sha256(output_file)
            if expected_checksum and current_checksum == expected_checksum:
                logger.info("Data already downloaded and checksum verified.")
                return {
                    "status": "skipped",
                    "file": str(output_file),
                    "checksum": current_checksum
                }

        # Download and save
        logger.info("Downloading and saving data...")
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        # Collect batches and write to parquet
        writer = None
        total_rows = 0
        
        for batch in ds:
            if writer is None:
                # Infer schema from first batch
                table = pa.Table.from_pydict(batch)
                writer = pq.ParquetWriter(output_file, table.schema)
            table = pa.Table.from_pydict(batch)
            writer.write_table(table)
            total_rows += len(table)
            if total_rows % 100000 == 0:
                logger.info(f"Downloaded {total_rows} rows...")
        
        if writer:
            writer.close()
        
        logger.info(f"Download complete. Total rows: {total_rows}")
        
        # Compute checksum
        final_checksum = compute_sha256(output_file)
        
        if expected_checksum and final_checksum != expected_checksum:
            logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {final_checksum}")
            raise ValueError("Checksum mismatch after download")
        
        return {
            "status": "downloaded",
            "file": str(output_file),
            "checksum": final_checksum,
            "rows": total_rows
        }

    except Exception as e:
        logger.error(f"Failed to download or verify data: {e}")
        raise

def archive_data(source_dir: Path, archive_dir: Path) -> List[Dict[str, str]]:
    """
    Copy downloaded data to archive directory and compute checksums.
    Returns list of checksum records.
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    checksums = []
    
    for file_path in source_dir.glob("*"):
        if file_path.is_file():
            dest_path = archive_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            checksum = compute_sha256(dest_path)
            checksums.append({
                "file": str(dest_path),
                "checksum": checksum
            })
            logger.info(f"Archived {file_path.name} with checksum {checksum}")
    
    return checksums

def ensure_data_available() -> bool:
    """
    Check if data is available in the expected location.
    """
    expected_files = [DATA_RAW_DIR / "ebird_data.parquet"]
    return all(f.exists() for f in expected_files)

def run_download_pipeline():
    """
    Main pipeline for downloading and verifying canonical data.
    Implements T005b.
    """
    logger.info("Starting download pipeline (T005b)")
    
    # 1. Check for full EBD availability (T005a result is assumed from previous step)
    # We prioritize the sample dataset if full EBD is not available
    # Based on plan, if full EBD is unavailable, we use vvud/eb-data
    
    dataset_to_use = SAMPLE_DATASET_ID
    logger.info(f"Using dataset: {dataset_to_use}")
    
    # 2. Verify dataset existence
    if not check_real_data_available(dataset_to_use):
        raise RuntimeError(f"Dataset {dataset_to_use} is not available. Cannot proceed.")
    
    # 3. Download and verify
    download_result = download_and_verify_data(
        dataset_id=dataset_to_use,
        output_dir=DATA_RAW_DIR,
        expected_checksum=None  # Checksums would be provided if known
    )
    
    # 4. Archive data
    checksums = archive_data(DATA_RAW_DIR, DATA_ARCHIVE_DIR)
    
    # 5. Write checksum manifest
    manifest_path = DATA_ARCHIVE_DIR / "checksums.json"
    import json
    with open(manifest_path, "w") as f:
        json.dump({"checksums": checksums, "dataset": dataset_to_use}, f, indent=2)
    
    logger.info(f"Download pipeline complete. Manifest written to {manifest_path}")
    return checksums

def main():
    """Entry point for the download script."""
    run_download_pipeline()

if __name__ == "__main__":
    main()
