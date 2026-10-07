"""
Aggregator module for T012g: Write Raw Data to Immutable Store.

This module consolidates fetched and scraped data, generates SHA256 checksums,
and writes ingestion status to the raw data directory.
"""
import os
import sys
import logging
import json
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from local project structure
# Note: config.py is in code/ directory, so we import from config
try:
    from config import get_data_raw_dir, get_data_processed_dir
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_data_raw_dir, get_data_processed_dir
    from utils.logger import get_logger

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logging.error(f"File not found for checksum: {file_path}")
        raise

def save_checksums(checksums: List[Dict[str, str]], checksum_file: Path) -> None:
    """Append checksums to the checksums.txt file."""
    with open(checksum_file, 'a') as f:
        for entry in checksums:
            f.write(f"{entry['checksum']}  {entry['filename']}\n")

def write_ingestion_status(status: Dict[str, Any], status_file: Path) -> None:
    """Write the ingestion status to a JSON file."""
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)

def aggregate_raw_data(
    api_fetched_path: Optional[Path],
    literature_scraped_path: Optional[Path],
    filtered_raw_path: Optional[Path],
    checksums_file: Path,
    status_file: Path
) -> Dict[str, Any]:
    """
    Aggregate raw data files, generate checksums, and write status.
    
    Args:
        api_fetched_path: Path to api_fetched.json (from T012a)
        literature_scraped_path: Path to literature_scraped.csv (from T012d-SLR-Exec)
        filtered_raw_path: Path to filtered_raw.csv (from T012d-Filter)
        checksums_file: Path to data/checksums.txt
        status_file: Path to data/raw/.ingestion_status.json
    
    Returns:
        Status dictionary containing success flags and file inventory.
    """
    logger = get_logger(__name__)
    successful_files = []
    failed_files = []
    checksums = []
    
    # File inventory mapping: logical name -> actual path
    file_inventory = {
        "api_fetched.json": api_fetched_path,
        "literature_scraped.csv": literature_scraped_path,
        "filtered_raw.csv": filtered_raw_path
    }
    
    for logical_name, file_path in file_inventory.items():
        if file_path and file_path.exists():
            try:
                checksum = calculate_sha256(file_path)
                checksums.append({
                    "filename": logical_name,
                    "checksum": checksum
                })
                successful_files.append(logical_name)
                logger.info(f"Checksummed: {logical_name} ({checksum[:16]}...)")
            except Exception as e:
                logger.error(f"Failed to checksum {logical_name}: {e}")
                failed_files.append(logical_name)
        elif file_path:
            # File was expected but doesn't exist (source failed)
            logger.warning(f"Expected file missing: {logical_name} (path: {file_path})")
            failed_files.append(logical_name)
        else:
            # File was not provided (source not run or skipped)
            logger.info(f"File not provided for checksum: {logical_name}")
    
    # Write checksums if any were generated
    if checksums:
        save_checksums(checksums, checksums_file)
        logger.info(f"Checksums written to {checksums_file}")
    
    # Determine partial success
    partial_success = len(failed_files) > 0 or len(successful_files) == 0
    if len(successful_files) == 0 and len(failed_files) == 0:
        # No files provided at all
        partial_success = False 
    
    status = {
        "timestamp": str(Path(__file__).parent.parent), # Placeholder for actual timestamp logic if needed
        "partial_success": partial_success,
        "successful_files": successful_files,
        "failed_files": failed_files,
        "file_inventory": {k: str(v) if v else None for k, v in file_inventory.items()}
    }
    
    # Ensure directory exists
    status_file.parent.mkdir(parents=True, exist_ok=True)
    write_ingestion_status(status, status_file)
    logger.info(f"Ingestion status written to {status_file}")
    
    return status

def main():
    """Main entry point for T012g."""
    logger = get_logger(__name__)
    logger.info("Starting T012g: Write Raw Data to Immutable Store")
    
    # Define paths based on project structure
    raw_dir = get_data_raw_dir()
    checksums_file = Path("data/checksums.txt")
    status_file = raw_dir / ".ingestion_status.json"
    
    # Paths to input files (outputs of previous tasks)
    api_fetched_path = raw_dir / "api_fetched.json"
    literature_scraped_path = raw_dir / "literature_scraped.csv"
    filtered_raw_path = raw_dir / "filtered_raw.csv"
    
    # Ensure raw directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Perform aggregation
    status = aggregate_raw_data(
        api_fetched_path=api_fetched_path,
        literature_scraped_path=literature_scraped_path,
        filtered_raw_path=filtered_raw_path,
        checksums_file=checksums_file,
        status_file=status_file
    )
    
    if status["partial_success"]:
        logger.warning("Ingestion completed with partial success. Check logs for failures.")
    else:
        logger.info("Ingestion completed successfully.")
        
    return status

if __name__ == "__main__":
    main()
