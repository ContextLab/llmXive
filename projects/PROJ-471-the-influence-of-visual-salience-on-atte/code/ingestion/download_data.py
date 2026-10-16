"""
Real-data ingestion script for the Visual Salience project.

This script downloads the OpenNeuro dataset ds003123. It attempts to use the
openneuro-py library first, and uses the Hugging Face 'datasets'
library if the primary method fails. 

It verifies the existence of the expected 'sub-' directory structure, computes
SHA-256 checksums for all downloaded files, and saves them to data/raw/checksums.json.
If all real-data fetch attempts fail, it raises a RuntimeError with the code 
DATA_MISSING_001 to enforce fail-loud semantics.
"""
import json
import hashlib
import logging
import os
from pathlib import Path
from datetime import datetime

import openneuro
from datasets import load_dataset
from config import get_paths
from utils.logging import get_logger
from utils.versioning import register_artifact

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def attempt_openneuro_download(dataset_id: str, target_dir: Path) -> bool:
    """Attempt to download using the openneuro library."""
    try:
        logger.info(f"Attempting download via openneuro-py for {dataset_id}...")
        openneuro.download(dataset=dataset_id, target_dir=str(target_dir))
        return True
    except Exception as e:
        logger.warning(f"openneuro-py download failed: {e}")
        return False

def attempt_hf_download(dataset_id: str, target_dir: Path) -> bool:
    """Attempt to download using the Hugging Face datasets library."""
    try:
        logger.info(f"Attempting download via Hugging Face datasets for openneuro/{dataset_id}...")
        ds = load_dataset(f"openneuro/{dataset_id}", trust_remote_code=True)
        
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        
        for split in ds.keys():
            split_data = ds[split]
            split_path = target_dir / split
            split_path.mkdir(exist_ok=True)
            
            df = split_data.to_pandas()
            df.to_csv(split_path / "data.csv", index=False)
            
            if 'subject' in df.columns or 'sub' in df.columns:
                col = 'subject' if 'subject' in df.columns else 'sub'
                for sub_id in df[col].unique():
                    sub_dir = split_path / f"{sub_id}"
                    sub_dir.mkdir(exist_ok=True)
                    sub_df = df[df[col] == sub_id]
                    sub_df.to_csv(sub_dir / "data.csv", index=False)
        
        return True
    except Exception as e:
        logger.warning(f"Hugging Face datasets download failed: {e}")
        return False

def main():
    """
    Main ingestion pipeline.
    """
    paths = get_paths()
    dataset_id = "ds003123"
    raw_dir = paths.DATA_RAW / dataset_id
    checksum_file = paths.DATA_RAW / "checksums.json"

    logger.info(f"Starting ingestion for OpenNeuro dataset: {dataset_id}")

    # Step 1: Download dataset using multiple real sources
    success = False
    if not raw_dir.exists() or not any(raw_dir.iterdir()):
        if attempt_openneuro_download(dataset_id, raw_dir):
            success = True
        elif attempt_hf_download(dataset_id, raw_dir):
            success = True
    else:
        logger.info("Dataset already exists on disk. Skipping download.")
        success = True

    if not success:
        logger.error(f"All real-data fetch attempts failed for {dataset_id}.")
        raise RuntimeError("DATA_MISSING_001: Real data fetch failed")

    # Step 2: Verify 'sub-' structure
    all_dirs = [p for p in raw_dir.rglob("*") if p.is_dir()]
    sub_dirs = [d for d in all_dirs if d.name.startswith("sub-")]
    
    if not sub_dirs:
        logger.error(f"Dataset {dataset_id} does not contain expected 'sub-' structure.")
        raise RuntimeError("DATA_MISSING_001: Real data fetch failed")
    
    logger.info(f"Verified structure: Found {len(sub_dirs)} subject directories.")

    # Step 3: Compute SHA-256 checksums
    logger.info("Computing checksums for all files in raw directory...")
    manifest = {
        "dataset_id": dataset_id,
        "timestamp": datetime.utcnow().isoformat(),
        "files": []
    }

    for root, _, files in os.walk(raw_dir):
        for filename in files:
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(paths.DATA_RAW)
            sha256 = compute_sha256(file_path)
            manifest["files"].append({
                "path": str(rel_path),
                "sha256": sha256,
                "size": file_path.stat().st_size
            })

    with open(checksum_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Checksum manifest written to {checksum_file}")
    register_artifact(checksum_file, artifact_type="checksum_manifest", description="SHA-256 manifest for ds003123")

    logger.info("Ingestion completed successfully.")

if __name__ == "__main__":
    main()
