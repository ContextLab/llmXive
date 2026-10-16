"""
Real-data ingestion script for the Visual Salience project.

This script verifies the presence of the OpenNeuro Moral Foundations Eye‑Tracking
Dataset (ds003123) in the expected raw data directory, computes SHA‑256 checksums
for all files, and writes a manifest to ``data/raw/checksums.json``. If the dataset
is not present, the script aborts with a clear ``RuntimeError`` (fail‑loud semantics).
No synthetic data fallback is performed.
"""
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import os

from config import get_paths
from utils.logging import get_logger
from utils.versioning import register_artifact

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main() -> None:
    """
    Main ingestion pipeline.

    Steps:
    1. Verify that the expected raw data directory exists and contains at least one file.
    2. Compute SHA‑256 checksums for every file under the raw directory.
    3. Write a manifest (including timestamps and file sizes) to ``checksums.json``.
    4. Register the manifest as an artifact.
    """
    paths = get_paths()
    dataset_id = "ds003123"
    raw_dir = paths.DATA_RAW / dataset_id
    checksum_file = paths.DATA_RAW / "checksums.json"

    logger.info(f"Starting ingestion verification for OpenNeuro dataset: {dataset_id}")

    # ----------------------------------------------------------------------
    # Step 1 – Verify dataset presence
    # ----------------------------------------------------------------------
    if not raw_dir.exists() or not any(p.is_file() for p in raw_dir.rglob("*")):
        logger.error(
            f"Dataset directory '{raw_dir}' is missing or empty. "
            "The pipeline requires the dataset to be placed manually. "
            "Abort with DATA_MISSING_001."
        )
        raise RuntimeError("DATA_MISSING_001: Dataset not found in the expected location.")

    logger.info(f"Dataset directory found: {raw_dir}")

    # ----------------------------------------------------------------------
    # Step 2 – Compute checksums
    # ----------------------------------------------------------------------
    logger.info("Computing SHA‑256 checksums for all files in the raw directory...")
    manifest = {
        "dataset_id": dataset_id,
        "timestamp": datetime.utcnow().isoformat(),
        "files": []
    }

    for file_path in raw_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(paths.DATA_RAW)
            sha256 = compute_sha256(file_path)
            manifest["files"].append({
                "path": str(rel_path),
                "sha256": sha256,
                "size": file_path.stat().st_size
            })

    # ----------------------------------------------------------------------
    # Step 3 – Write manifest
    # ----------------------------------------------------------------------
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with checksum_file.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Checksum manifest written to {checksum_file}")

    # ----------------------------------------------------------------------
    # Step 4 – Register artifact
    # ----------------------------------------------------------------------
    register_artifact(
        file_path=checksum_file,
        artifact_type="checksum_manifest",
        description="SHA‑256 manifest for OpenNeuro ds003123"
    )

    logger.info("Ingestion verification completed successfully.")

if __name__ == "__main__":
    main()
