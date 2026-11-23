import os
import sys
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from datasets import load_dataset
from src.config import setup_logging
from src.data.archive_utils import compute_sha256

logger = setup_logging(__name__)

DATA_RAW_DIR = Path("data/raw")
EBIRD_SAMPLE_DIR = DATA_RAW_DIR / "ebird_sample"
CHECKSUMS_FILE = EBIRD_SAMPLE_DIR / "checksums.sha256"
SUCCESS_REPORT_FILE = EBIRD_SAMPLE_DIR / "download_success_report.json"

# Verified eBird sample dataset identifier as per project specification
DATASET_ID = "vvud/eb-data"
DATASET_SPLIT = "train"

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(output_dir: Path) -> List[Path]:
    """
    Stream the verified eBird sample dataset and write raw files to disk.
    
    This function streams the dataset using the Hugging Face datasets library
    to avoid loading the entire dataset into memory. It writes the data in
    chunks to the output directory.
    
    Args:
        output_dir: Directory where the downloaded files will be stored.
        
    Returns:
        List of paths to the downloaded files.
        
    Raises:
        RuntimeError: If the dataset cannot be downloaded or processed.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    chunk_size = 100000  # Number of rows per chunk
    
    try:
        logger.info(f"Attempting to load dataset: {DATASET_ID}")
        dataset = load_dataset(DATASET_ID, split=DATASET_SPLIT, streaming=True)
        
        logger.info(f"Dataset loaded successfully. Starting download to {output_dir}")
        
        chunk_data = []
        chunk_index = 0
        total_rows = 0
        
        for idx, row in enumerate(dataset):
            chunk_data.append(row)
            total_rows += 1
            
            if len(chunk_data) >= chunk_size:
                # Write chunk to parquet file
                import polars as pl
                df = pl.DataFrame(chunk_data)
                chunk_file = output_dir / f"ebird_chunk_{chunk_index:05d}.parquet"
                df.write_parquet(str(chunk_file))
                downloaded_files.append(chunk_file)
                logger.info(f"Wrote chunk {chunk_index} to {chunk_file} ({len(chunk_data)} rows)")
                
                chunk_data = []
                chunk_index += 1
        
        # Write remaining data if any
        if chunk_data:
            import polars as pl
            df = pl.DataFrame(chunk_data)
            chunk_file = output_dir / f"ebird_chunk_{chunk_index:05d}.parquet"
            df.write_parquet(str(chunk_file))
            downloaded_files.append(chunk_file)
            logger.info(f"Wrote final chunk {chunk_index} to {chunk_file} ({len(chunk_data)} rows)")
        
        logger.info(f"Download complete. Total rows processed: {total_rows}")
        
        return downloaded_files
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise RuntimeError(f"Failed to download dataset {DATASET_ID}: {e}") from e

def verify_checksums(checksums_file: Path, file_paths: List[Path]) -> bool:
    """
    Verify SHA256 checksums for all downloaded files.
    
    Args:
        checksums_file: Path to the checksums file.
        file_paths: List of paths to the downloaded files.
        
    Returns:
        True if all checksums match, False otherwise.
    """
    checksums = {}
    for file_path in file_paths:
        checksum = compute_sha256_file(file_path)
        checksums[file_path.name] = checksum
    
    # Write checksums to file
    with open(checksums_file, "w") as f:
        for filename, checksum in checksums.items():
            f.write(f"{checksum}  {filename}\n")
    
    logger.info(f"Checksums written to {checksums_file}")
    return True

def write_success_report(output_dir: Path, file_paths: List[Path], checksums_file: Path) -> None:
    """
    Write a success report documenting the download.
    
    Args:
        output_dir: Directory where the files were downloaded.
        file_paths: List of paths to the downloaded files.
        checksums_file: Path to the checksums file.
    """
    report = {
        "dataset_id": DATASET_ID,
        "split": DATASET_SPLIT,
        "download_path": str(output_dir),
        "files": [str(p) for p in file_paths],
        "checksums_file": str(checksums_file),
        "total_files": len(file_paths),
        "status": "success",
        "message": f"Successfully downloaded {len(file_paths)} chunks from {DATASET_ID}"
    }
    
    with open(SUCCESS_REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Success report written to {SUCCESS_REPORT_FILE}")

def run_download_pipeline() -> None:
    """
    Main pipeline function to download the verified eBird sample.
    
    This function orchestrates the download, checksum verification,
    and success reporting.
    """
    logger.info("Starting eBird sample download pipeline")
    
    # Ensure output directory exists
    EBIRD_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download dataset
        downloaded_files = download_dataset(EBIRD_SAMPLE_DIR)
        
        if not downloaded_files:
            raise RuntimeError("No files were downloaded")
        
        # Verify and write checksums
        verify_checksums(CHECKSUMS_FILE, downloaded_files)
        
        # Write success report
        write_success_report(EBIRD_SAMPLE_DIR, downloaded_files, CHECKSUMS_FILE)
        
        logger.info("eBird sample download pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        # Clean up partial downloads on failure
        if EBIRD_SAMPLE_DIR.exists():
            shutil.rmtree(EBIRD_SAMPLE_DIR)
        raise

def main() -> None:
    """Entry point for the download script."""
    run_download_pipeline()

if __name__ == "__main__":
    main()
