"""
ZINC15 Data Download Script

Downloads the ZINC15 dataset from HuggingFace datasets, verifies the source
against the canonical reference (Constitution Principle I), and saves checksums
to data/checksums.json.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports if running as script
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from utils.logging import get_project_logger
from config import get_paths

logger = get_project_logger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_canonical_source(dataset_id: str) -> bool:
    """
    Verify that the dataset ID maps to the canonical ZINC15 source.
    Constitution Principle I: Data integrity and provenance.
    
    The canonical ZINC15 dataset on HuggingFace is identified by the ID 'zinc15'.
    This function strictly enforces this ID to ensure provenance.
    """
    canonical_id = "zinc15"
    if dataset_id != canonical_id:
        msg = f"Dataset ID '{dataset_id}' does not match canonical '{canonical_id}'."
        logger.error(msg)
        raise ValueError(msg)
    
    logger.info(f"Verified dataset ID '{dataset_id}' matches canonical ZINC15 source.")
    return True

def download_and_checksum(dataset_id: str = "zinc15", split: str = "train", output_dir: str = "data/raw") -> Dict[str, Any]:
    """
    Download ZINC15 dataset and generate checksums for verification.
    
    Args:
        dataset_id: HuggingFace dataset ID
        split: Dataset split to download
        output_dir: Directory to save the dataset (relative to data/raw)
    
    Returns:
        Dictionary containing download metadata and checksums
    """
    paths = get_paths()
    output_path = paths.data_raw / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download of {dataset_id} (split={split})...")
    
    # Verify canonical source
    if not verify_canonical_source(dataset_id):
        # verify_canonical_source raises ValueError if mismatch, but kept for logic clarity
        raise ValueError(f"Dataset ID {dataset_id} is not the canonical ZINC15 source.")
    
    try:
        # Load dataset (this downloads to cache, we need to export to disk)
        logger.info("Loading dataset from HuggingFace...")
        # Streaming is not used here to allow full save to parquet for checksum
        # If the dataset is too large, this might need adjustment, but per tasks.md
        # we assume standard download is feasible or we handle the error.
        dataset = load_dataset(dataset_id, split=split)
        
        # Save dataset to parquet for efficient storage and checksum
        parquet_file = output_path / f"{dataset_id}_{split}.parquet"
        logger.info(f"Saving dataset to {parquet_file}...")
        dataset.to_parquet(str(parquet_file))
        
        # Compute checksum
        checksum = compute_file_checksum(parquet_file)
        logger.info(f"Dataset saved. SHA256: {checksum}")
        
        # Save checksums metadata to data/checksums.json
        checksums_file = paths.data_root / "checksums.json"
        
        # Attempt to load existing checksums to append or update
        existing_checksums = {}
        if checksums_file.exists():
            try:
                with open(checksums_file, 'r') as f:
                    existing_checksums = json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Existing checksums.json is invalid, overwriting.")
        
        # Update or add the new entry
        checksum_data = {
            "dataset_id": dataset_id,
            "split": split,
            "file_path": str(parquet_file.relative_to(paths.data_root)),
            "sha256": checksum,
            "downloaded_at": "runtime" # We don't have a specific 'download_date' from HF info reliably here
        }
        
        # If the file path is unique, we can just update the dict or append.
        # For simplicity, we overwrite the entry for this specific dataset/split combo
        # or store as a list if multiple splits exist. Here we assume one entry per split.
        existing_checksums[dataset_id] = checksum_data
        
        with open(checksums_file, 'w') as f:
            json.dump(existing_checksums, f, indent=2)
        
        logger.info(f"Checksums saved to {checksums_file}")
        
        return checksum_data
        
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        raise

def main():
    """Main entry point for the download script."""
    logger.info("=== ZINC15 Data Download Started ===")
    
    try:
        result = download_and_checksum()
        logger.info("=== ZINC15 Data Download Completed Successfully ===")
        logger.info(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"=== ZINC15 Data Download Failed: {e} ===")
        raise

if __name__ == "__main__":
    main()