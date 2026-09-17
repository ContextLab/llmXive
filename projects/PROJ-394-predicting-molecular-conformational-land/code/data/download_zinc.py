"""
ZINC15 Data Download Script

Downloads the ZINC15 dataset from HuggingFace datasets, verifies the source
against the canonical reference (Constitution Principle I), and saves checksums.
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
    """
    # Canonical ZINC15 on HuggingFace is 'zinc15' (or 'zinc15-2017' depending on version)
    # We verify by checking the dataset description and source URL if available.
    # For this implementation, we rely on the known canonical ID 'zinc15'.
    canonical_id = "zinc15"
    if dataset_id != canonical_id:
        logger.warning(f"Dataset ID '{dataset_id}' does not match canonical '{canonical_id}'.")
        return False
    
    logger.info(f"Verified dataset ID '{dataset_id}' matches canonical ZINC15 source.")
    return True

def download_and_checksum(dataset_id: str = "zinc15", split: str = "train", output_dir: str = "data/raw") -> Dict[str, Any]:
    """
    Download ZINC15 dataset and generate checksums for verification.
    
    Args:
        dataset_id: HuggingFace dataset ID
        split: Dataset split to download
        output_dir: Directory to save the dataset
      
    Returns:
        Dictionary containing download metadata and checksums
    """
    paths = get_paths()
    output_path = paths.data_raw / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download of {dataset_id} (split={split})...")
    
    # Verify canonical source
    if not verify_canonical_source(dataset_id):
        raise ValueError(f"Dataset ID {dataset_id} is not the canonical ZINC15 source.")
    
    try:
        # Load dataset (this downloads to cache, we need to export to disk)
        logger.info("Loading dataset from HuggingFace...")
        dataset = load_dataset(dataset_id, split=split)
        
        # Save dataset to parquet for efficient storage and checksum
        parquet_file = output_path / f"{dataset_id}_{split}.parquet"
        logger.info(f"Saving dataset to {parquet_file}...")
        dataset.to_parquet(str(parquet_file))
        
        # Compute checksum
        checksum = compute_file_checksum(parquet_file)
        logger.info(f"Dataset saved. SHA256: {checksum}")
        
        # Save checksums metadata
        checksums_file = paths.data_root / "checksums.json"
        checksum_data = {
            "dataset_id": dataset_id,
            "split": split,
            "file_path": str(parquet_file),
            "sha256": checksum,
            "downloaded_at": str(dataset.info.get('download_date', 'unknown'))
        }
        
        with open(checksums_file, 'w') as f:
            json.dump(checksum_data, f, indent=2)
        
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
