"""
Real-data ingestion script for the Visual Salience project.

This script downloads the OpenNeuro dataset ds003123 using the openneuro-py library.
It verifies the existence of the expected 'sub-' directory structure, computes
SHA-256 checksums for all downloaded files, and saves them to data/raw/checksums.json.
If any part of the process fails, it raises a RuntimeError with the code 
DATA_MISSING_001 to enforce fail-loud semantics.
"""
import json
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import openneuro
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

def main():
    """
    Main ingestion pipeline.
    """
    paths = get_paths()
    dataset_id = "ds003123"
    raw_dir = paths.DATA_RAW / dataset_id
    checksum_file = paths.DATA_RAW / "checksums.json"

    logger.info(f"Starting ingestion for OpenNeuro dataset: {dataset_id}")

    try:
        # Step 1: Download dataset
        # openneuro.download handles directory creation and fetching
        logger.info(f"Downloading dataset {dataset_id} to {raw_dir}...")
        openneuro.download(dataset=dataset_id, target_dir=str(raw_dir))

        if not raw_dir.exists() or not any(raw_dir.iterdir()):
            raise RuntimeError("Downloaded directory is empty or does not exist.")

        # Step 2: Verify 'sub-' structure
        # The dataset is expected to have directories for subjects (sub-01, etc.)
        sub_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
        if not sub_dirs:
            logger.error(f"Dataset {dataset_id} does not contain expected 'sub-' structure.")
            raise RuntimeError("Expected 'sub-' structure not found in raw data.")
        
        logger.info(f"Verified structure: Found {len(sub_dirs)} subject directories.")

        # Step 3: Compute SHA-256 checksums
        logger.info("Computing checksums for all files in raw directory...")
        manifest = {
            "dataset_id": dataset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "files": []
        }

        # Walk through all files in the dataset directory
        for root, _, files in os.walk(raw_dir):
            for filename in files:
                file_path = Path(root) / filename
                # Relative path for the manifest
                rel_path = file_path.relative_to(paths.DATA_RAW)
                sha256 = compute_sha256(file_path)
                manifest["files"].append({
                    "path": str(rel_path),
                    "sha256": sha256,
                    "size": file_path.stat().st_size
                })

        # Write manifest to data/raw/checksums.json
        with open(checksum_file, "w") as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Checksum manifest written to {checksum_file}")
        register_artifact(checksum_file, artifact_type="checksum_manifest", description="SHA-256 manifest for ds003123")

        logger.info("Ingestion completed successfully.")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        # Enforce the exact error code required by the task
        raise RuntimeError("DATA_MISSING_001: Real data fetch failed") from e

if __name__ == "__main__":
    main()
