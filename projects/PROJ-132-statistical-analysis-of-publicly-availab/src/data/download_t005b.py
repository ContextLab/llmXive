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

# Configure logging
logger = setup_logging("download_t005b")

DATASET_NAME = "vvud/eb-data"
RAW_DATA_DIR = Path("data/raw/ebird_sample")
CHECKSUMS_FILE = RAW_DATA_DIR / "checksums.sha256"
SUCCESS_REPORT_FILE = Path("data/provenance/download_success_report.json")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(dataset_name: str, output_dir: Path, streaming: bool = True) -> List[Path]:
    """
    Stream the verified eBird sample dataset and save files to output_dir.
    
    Args:
        dataset_name: HuggingFace dataset name
        output_dir: Directory to save downloaded files
        streaming: Whether to stream the dataset (True for memory efficiency)
    
    Returns:
        List of paths to downloaded files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Attempting to download dataset: {dataset_name}")
    
    try:
        # Load dataset with streaming to handle large data
        dataset = load_dataset(dataset_name, split="train", streaming=streaming)
        
        downloaded_files = []
        
        # Stream and save chunks as files
        chunk_size = 100000  # Rows per chunk
        chunk_idx = 0
        current_chunk = []
        
        for idx, record in enumerate(dataset):
            current_chunk.append(record)
            
            if len(current_chunk) >= chunk_size:
                # Write chunk to file
                chunk_file = output_dir / f"ebird_chunk_{chunk_idx:04d}.parquet"
                # Convert to pandas for parquet writing
                import pandas as pd
                df_chunk = pd.DataFrame(current_chunk)
                df_chunk.to_parquet(chunk_file, index=False)
                downloaded_files.append(chunk_file)
                logger.info(f"Written chunk {chunk_idx} to {chunk_file}")
                
                current_chunk = []
                chunk_idx += 1
            
            # Progress logging
            if (idx + 1) % 500000 == 0:
                logger.info(f"Processed {idx + 1} records...")
        
        # Write remaining records
        if current_chunk:
            chunk_file = output_dir / f"ebird_chunk_{chunk_idx:04d}.parquet"
            import pandas as pd
            df_chunk = pd.DataFrame(current_chunk)
            df_chunk.to_parquet(chunk_file, index=False)
            downloaded_files.append(chunk_file)
            logger.info(f"Written final chunk {chunk_idx} to {chunk_file}")
        
        logger.info(f"Successfully downloaded {len(downloaded_files)} chunks")
        return downloaded_files
        
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {str(e)}")
        raise RuntimeError(f"Dataset download failed: {str(e)}")

def verify_checksums(files: List[Path], checksums_file: Path) -> Dict[str, str]:
    """
    Compute and store SHA-256 checksums for all downloaded files.
    
    Args:
        files: List of file paths to checksum
        checksums_file: Path to write checksums file
    
    Returns:
        Dictionary mapping filenames to their checksums
    """
    checksums = {}
    
    for file_path in files:
        checksum = compute_sha256(file_path)
        checksums[file_path.name] = checksum
        logger.info(f"Checksum for {file_path.name}: {checksum}")
    
    # Write checksums to file
    with open(checksums_file, "w") as f:
        for filename, checksum in checksums.items():
            f.write(f"{checksum}  {filename}\n")
    
    logger.info(f"Checksums written to {checksums_file}")
    return checksums

def archive_data(source_dir: Path, archive_dir: Path) -> None:
    """
    Copy downloaded data to archive directory.
    
    Args:
        source_dir: Source directory with downloaded files
        archive_dir: Destination archive directory
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all files from source to archive
    for file_path in source_dir.iterdir():
        if file_path.is_file():
            shutil.copy2(file_path, archive_dir / file_path.name)
            logger.info(f"Archived {file_path.name} to {archive_dir}")
    
    # Copy checksums file
    if CHECKSUMS_FILE.exists():
        shutil.copy2(CHECKSUMS_FILE, archive_dir / "checksums.sha256")
        logger.info(f"Archived checksums to {archive_dir}")

def write_success_report(
    dataset_name: str,
    downloaded_files: List[Path],
    checksums: Dict[str, str],
    output_dir: Path,
    archive_dir: Path
) -> None:
    """
    Write a success report documenting the download.
    
    Args:
        dataset_name: Name of the dataset
        downloaded_files: List of downloaded file paths
        checksums: Dictionary of filename -> checksum
        output_dir: Directory where files were saved
        archive_dir: Directory where files were archived
    """
    report = {
        "dataset_name": dataset_name,
        "timestamp": None,  # Will be set by caller
        "download_status": "success",
        "output_directory": str(output_dir),
        "archive_directory": str(archive_dir),
        "files_downloaded": len(downloaded_files),
        "file_details": [
            {
                "filename": f.name,
                "path": str(f),
                "checksum": checksums.get(f.name, "unknown")
            }
            for f in downloaded_files
        ],
        "total_size_bytes": sum(f.stat().st_size for f in downloaded_files if f.exists())
    }
    
    # Add timestamp
    from datetime import datetime, timezone
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Ensure provenance directory exists
    SUCCESS_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(SUCCESS_REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Success report written to {SUCCESS_REPORT_FILE}")

def run_download_pipeline() -> Dict[str, Any]:
    """
    Execute the full download pipeline for T005b.
    
    Returns:
        Dictionary with pipeline execution results
    """
    logger.info("Starting eBird sample download pipeline (T005b)")
    
    # Step 1: Download dataset
    downloaded_files = download_dataset(DATASET_NAME, RAW_DATA_DIR)
    
    if not downloaded_files:
        raise RuntimeError("No files were downloaded from the dataset")
    
    # Step 2: Verify checksums
    checksums = verify_checksums(downloaded_files, CHECKSUMS_FILE)
    
    # Step 3: Archive data
    archive_dir = Path("data/raw/archive/ebird_sample")
    archive_data(RAW_DATA_DIR, archive_dir)
    
    # Step 4: Write success report
    write_success_report(
        dataset_name=DATASET_NAME,
        downloaded_files=downloaded_files,
        checksums=checksums,
        output_dir=RAW_DATA_DIR,
        archive_dir=archive_dir
    )
    
    logger.info("eBird sample download pipeline completed successfully")
    
    return {
        "status": "success",
        "files_downloaded": len(downloaded_files),
        "output_dir": str(RAW_DATA_DIR),
        "archive_dir": str(archive_dir),
        "checksums_file": str(CHECKSUMS_FILE),
        "report_file": str(SUCCESS_REPORT_FILE)
    }

def main():
    """Main entry point for the download script."""
    try:
        result = run_download_pipeline()
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
