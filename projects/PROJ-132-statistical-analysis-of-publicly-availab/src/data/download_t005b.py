"""
T005b: Download Verified eBird Sample (vvud/eb-data)

This script streams the verified eBird sample dataset using the Hugging Face
datasets library with streaming enabled to minimize memory usage. It writes
the raw files to data/raw/ebird_sample/, computes SHA-256 checksums for each
shard, and stores them in checksums.sha256.

Requirements:
- datasets>=2.14.0
- No synthetic fallback: aborts on any download error.
"""

import os
import sys
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path for imports if running as script
if 'code' in os.getcwd():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datasets import load_dataset
from src.config import setup_logging

# Configure logging
logger = setup_logging("download_t005b")

# Constants
DATASET_NAME = "vvud/eb-data"
SPLIT = "train"
OUTPUT_DIR = Path("data/raw/ebird_sample")
CHECKSUM_FILE = OUTPUT_DIR / "checksums.sha256"
CHUNK_SIZE = 100_000  # Rows per chunk for streaming


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise


def download_dataset() -> Dict[str, Any]:
    """
    Stream the verified eBird sample dataset and save to disk.
    
    Returns:
        Dict with metadata about the download operation.
        
    Raises:
        RuntimeError: If dataset is not available or download fails.
        FileNotFoundError: If dataset name is not found.
    """
    logger.info(f"Attempting to download dataset: {DATASET_NAME}")
    
    # Verify dataset exists first
    try:
        from datasets import get_dataset_names
        available_datasets = get_dataset_names()
        if DATASET_NAME not in available_datasets:
            error_msg = f"Dataset '{DATASET_NAME}' not found in Hugging Face Hub. Aborting."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
    except Exception as e:
        error_msg = f"Failed to verify dataset availability: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    # Track downloaded files and their checksums
    downloaded_files: List[Dict[str, Any]] = []
    
    try:
        # Load dataset with streaming enabled
        logger.info(f"Loading dataset with streaming: {DATASET_NAME}")
        dataset = load_dataset(DATASET_NAME, split=SPLIT, streaming=True)
        
        # Process in chunks and save to parquet files
        chunk_count = 0
        current_chunk = []
        
        logger.info("Starting data streaming and saving...")
        
        for idx, record in enumerate(dataset):
            current_chunk.append(record)
            
            if len(current_chunk) >= CHUNK_SIZE:
                chunk_count += 1
                chunk_file = OUTPUT_DIR / f"ebird_chunk_{chunk_count:04d}.parquet"
                
                try:
                    import pandas as pd
                    df_chunk = pd.DataFrame(current_chunk)
                    df_chunk.to_parquet(chunk_file, index=False)
                    
                    # Compute checksum
                    checksum = compute_sha256(chunk_file)
                    downloaded_files.append({
                        "filename": chunk_file.name,
                        "sha256": checksum,
                        "rows": len(current_chunk)
                    })
                    
                    logger.info(f"Saved chunk {chunk_count}: {chunk_file.name} "
                                f"({len(current_chunk)} rows, checksum: {checksum[:16]}...)")
                    
                    current_chunk = []
                except Exception as e:
                    error_msg = f"Failed to save chunk {chunk_count}: {str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        
        # Save remaining records
        if current_chunk:
            chunk_count += 1
            chunk_file = OUTPUT_DIR / f"ebird_chunk_{chunk_count:04d}.parquet"
            
            try:
                import pandas as pd
                df_chunk = pd.DataFrame(current_chunk)
                df_chunk.to_parquet(chunk_file, index=False)
                
                checksum = compute_sha256(chunk_file)
                downloaded_files.append({
                    "filename": chunk_file.name,
                    "sha256": checksum,
                    "rows": len(current_chunk)
                })
                
                logger.info(f"Saved final chunk {chunk_count}: {chunk_file.name} "
                            f"({len(current_chunk)} rows, checksum: {checksum[:16]}...)")
            except Exception as e:
                error_msg = f"Failed to save final chunk: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        if chunk_count == 0:
            error_msg = "No data was downloaded. Dataset might be empty."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"Successfully downloaded {chunk_count} chunks with {sum(f['rows'] for f in downloaded_files)} total rows")
        
        # Write checksums file
        write_checksums(downloaded_files)
        
        return {
            "dataset_name": DATASET_NAME,
            "split": SPLIT,
            "chunks_downloaded": chunk_count,
            "total_rows": sum(f['rows'] for f in downloaded_files),
            "files": downloaded_files,
            "output_dir": str(OUTPUT_DIR)
        }
        
    except FileNotFoundError:
        # Re-raise file not found errors (dataset not available)
        raise
    except Exception as e:
        error_msg = f"Failed to download dataset: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def write_checksums(files: List[Dict[str, Any]]) -> None:
    """Write checksums to a file in standard sha256sum format."""
    try:
        with open(CHECKSUM_FILE, 'w') as f:
            for file_info in files:
                f.write(f"{file_info['sha256']}  {file_info['filename']}\n")
        logger.info(f"Checksums written to {CHECKSUM_FILE}")
    except Exception as e:
        error_msg = f"Failed to write checksums file: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def verify_checksums() -> bool:
    """Verify all downloaded files against their checksums."""
    if not CHECKSUM_FILE.exists():
        logger.error(f"Checksum file not found: {CHECKSUM_FILE}")
        return False
    
    logger.info(f"Verifying checksums from {CHECKSUM_FILE}")
    
    try:
        with open(CHECKSUM_FILE, 'r') as f:
            lines = f.readlines()
        
        all_valid = True
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('  ')
            if len(parts) != 2:
                logger.warning(f"Invalid checksum line: {line}")
                all_valid = False
                continue
            
            expected_hash, filename = parts
            file_path = OUTPUT_DIR / filename
            
            if not file_path.exists():
                logger.error(f"File missing for checksum verification: {filename}")
                all_valid = False
                continue
            
                computed_hash = compute_sha256(file_path)
                if computed_hash != expected_hash:
                    logger.error(f"Checksum mismatch for {filename}: "
                                f"expected {expected_hash}, got {computed_hash}")
                    all_valid = False
                else:
                    logger.info(f"Checksum valid: {filename}")
    
        return all_valid
        
    except Exception as e:
        logger.error(f"Failed to verify checksums: {str(e)}")
        return False


def archive_data() -> None:
    """Copy downloaded data to archive directory."""
    archive_dir = Path("data/raw/archive")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Archiving data to {archive_dir}")
    
    try:
        for file_path in OUTPUT_DIR.glob("*"):
            if file_path.is_file():
                shutil.copy2(file_path, archive_dir / file_path.name)
        logger.info("Data archived successfully")
    except Exception as e:
        logger.error(f"Failed to archive data: {str(e)}")
        raise RuntimeError(f"Archive failed: {str(e)}")


def write_success_report(report_data: Dict[str, Any]) -> None:
    """Write a success report to data/provenance."""
    provenance_dir = Path("data/provenance")
    provenance_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = provenance_dir / "ebird_download_report.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        logger.info(f"Success report written to {report_file}")
    except Exception as e:
        logger.error(f"Failed to write success report: {str(e)}")
        raise RuntimeError(f"Report write failed: {str(e)}")


def run_download_pipeline() -> Dict[str, Any]:
    """Run the complete download pipeline."""
    logger.info("Starting eBird sample download pipeline")
    
    try:
        # Download dataset
        download_report = download_dataset()
        
        # Verify checksums
        if not verify_checksums():
            raise RuntimeError("Checksum verification failed")
        
        # Archive data
        archive_data()
        
        # Write success report
        write_success_report(download_report)
        
        logger.info("Download pipeline completed successfully")
        return download_report
        
    except Exception as e:
        logger.error(f"Download pipeline failed: {str(e)}")
        raise


def main():
    """Main entry point."""
    logger.info("T005b: Download Verified eBird Sample")
    
    try:
        result = run_download_pipeline()
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
