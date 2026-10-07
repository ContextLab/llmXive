"""
Compute SHA-256 checksums for ALL downloaded datasets in data/raw/
and write results to data/checksums.csv (FR-010).

CRITICAL: This script runs immediately after T013 (download_datasets.py)
on the data/raw/ directory to cover every downloaded dataset, regardless
of subsequent filtering outcomes.
"""
import os
import sys
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging_config import setup_pipeline_logger

# Setup logger
logger = setup_pipeline_logger("checksum_datasets")

# Target directories and files as per project structure
RAW_DIR = project_root / "data" / "raw"
CHECKSUMS_FILE = project_root / "data" / "checksums.csv"
DATASETS_CSV = project_root / "data" / "datasets.csv"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        raise

def get_raw_dataset_files() -> List[Path]:
    """Get all dataset files in the raw directory."""
    if not RAW_DIR.exists():
        logger.error(f"Raw directory does not exist: {RAW_DIR}")
        logger.error("Please run T013 (download_datasets.py) first to populate data/raw/")
        sys.exit(1)
    
    files = []
    # Scan for common data extensions
    for ext in ["*.csv", "*.arff", "*.txt", "*.parquet", "*.json"]:
        files.extend(RAW_DIR.glob(ext))
    
    # Filter out log files and metadata files
    filtered_files = [
        f for f in files 
        if not f.name.startswith("log") 
        and not f.name.startswith("filter_")
        and not f.name.startswith("checksums")
        and not f.name.startswith("datasets")
    ]
    
    logger.info(f"Found {len(filtered_files)} dataset files in {RAW_DIR}")
    return filtered_files

def get_dataset_id_from_filename(file_path: Path) -> str:
    """Extract dataset ID from filename."""
    # Expected formats: dataset_{id}.csv, {id}.csv, or {id}.arff
    name = file_path.stem
    if name.startswith("dataset_"):
        return name[8:]  # Remove "dataset_" prefix
    return name

def write_checksums_csv(checksums: List[Dict[str, Any]]) -> None:
    """Write checksums to CSV file."""
    if not checksums:
        logger.warning("No checksums to write")
        # Still create the file with headers to satisfy file existence requirements
        with open(CHECKSUMS_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["dataset_id", "file_path", "sha256", "file_size_bytes"])
            writer.writeheader()
        return
    
    headers = ["dataset_id", "file_path", "sha256", "file_size_bytes"]
    
    with open(CHECKSUMS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(checksums)
    
    logger.info(f"Wrote {len(checksums)} checksums to {CHECKSUMS_FILE}")

def update_datasets_csv_with_checksums(checksums: List[Dict[str, Any]]) -> None:
    """Update datasets.csv with checksum information for downloaded datasets."""
    if not DATASETS_CSV.exists():
        logger.warning(f"{DATASETS_CSV} does not exist, skipping update")
        return
    
    # Read existing datasets
    with open(DATASETS_CSV, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    if not fieldnames:
        logger.warning("Datasets CSV has no headers")
        return

    # Create lookup for checksums
    checksum_lookup = {c["dataset_id"]: c["sha256"] for c in checksums}
    
    # Update rows with checksums
    updated_rows = []
    for row in rows:
        dataset_id = row.get("dataset_id", "")
        if dataset_id in checksum_lookup:
            row["checksum"] = checksum_lookup[dataset_id]
        updated_rows.append(row)
    
    # Write back
    if updated_rows:
        with open(DATASETS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)
        logger.info(f"Updated {len(updated_rows)} rows in {DATASETS_CSV}")

def main():
    """Main function to compute checksums for ALL downloaded datasets in data/raw/."""
    logger.info("Starting checksum computation for ALL downloaded datasets in data/raw/")
    
    # Verify raw directory exists (T013 dependency)
    if not RAW_DIR.exists():
        logger.error(f"Raw directory does not exist: {RAW_DIR}")
        logger.error("Please run T013 (download_datasets.py) first to populate data/raw/")
        sys.exit(1)
    
    # Get all dataset files in raw directory
    dataset_files = get_raw_dataset_files()
    
    if not dataset_files:
        logger.warning("No dataset files found in raw directory")
        # Create empty checksums file with headers
        with open(CHECKSUMS_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["dataset_id", "file_path", "sha256", "file_size_bytes"])
            writer.writeheader()
        sys.exit(1)
    
    # Compute checksums
    checksums = []
    success_count = 0
    for file_path in dataset_files:
        try:
            dataset_id = get_dataset_id_from_filename(file_path)
            sha256 = compute_sha256(file_path)
            file_size = file_path.stat().st_size
            
            checksums.append({
                "dataset_id": dataset_id,
                "file_path": str(file_path.relative_to(project_root)),
                "sha256": sha256,
                "file_size_bytes": file_size
            })
            
            success_count += 1
            logger.info(f"Checksummed {dataset_id}: {sha256[:16]}... ({file_size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            continue
    
    if not checksums:
        logger.error("No checksums were successfully computed")
        sys.exit(1)
    
    logger.info(f"Successfully checksummed {success_count}/{len(dataset_files)} files")
    
    # Write checksums to CSV
    write_checksums_csv(checksums)
    
    # Update datasets.csv with checksum information
    update_datasets_csv_with_checksums(checksums)
    
    logger.info("Checksum computation completed successfully")
    logger.info(f"Results written to {CHECKSUMS_FILE}")

if __name__ == "__main__":
    main()