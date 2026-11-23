"""Download HCP data with checksum verification."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from config import get_paths, ensure_dirs
from utils.logging import get_logger, log_operation

logger = get_logger("download_hcp")


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_hash(file_path: str) -> str:
    """Get file hash (alias for compute_sha256)."""
    return compute_sha256(file_path)


def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file checksum."""
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash


def save_manifest(manifest_path: str, files: Dict[str, str]) -> None:
    """Save manifest of downloaded files with checksums."""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(files, f, indent=2)


def load_manifest(manifest_path: str) -> Dict[str, str]:
    """Load manifest of downloaded files."""
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            return json.load(f)
    return {}


def fetch_behavioral_data_hcp_data() -> pd.DataFrame:
    """Fetch behavioral data using hcp_data package."""
    try:
        from hcp_data import load_behavioral
        df = load_behavioral()
        # Ensure required columns exist
        if 'Sleep_Score' not in df.columns or 'Framewise_Displacement' not in df.columns:
            raise ValueError("Missing required columns in behavioral data")
        return df
    except ImportError:
        raise RuntimeError("hcp_data package not installed. Install with: pip install hcp_data")


def fetch_behavioral_data_backup() -> pd.DataFrame:
    """Backup method: load from datasets package."""
    try:
        from datasets import load_dataset
        ds = load_dataset('hcp1200', split='train')
        df = ds.to_pandas()
        # Ensure required columns exist
        if 'Sleep_Score' not in df.columns or 'Framewise_Displacement' not in df.columns:
            raise ValueError("Missing required columns in behavioral data")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load backup dataset: {e}")


def fetch_behavioral_data() -> pd.DataFrame:
    """Fetch behavioral data with fallback."""
    logger.log_operation("fetch_behavioral_data", params={"method": "hcp_data"})
    try:
        return fetch_behavioral_data_hcp_data()
    except Exception as e:
        logger.log_operation("fetch_behavioral_data_fallback", params={"error": str(e)})
        return fetch_behavioral_data_backup()


def download_cifti_files(subject_ids: List[str], output_dir: str) -> Dict[str, str]:
    """Download CIFTI files for subjects."""
    files = {}
    for sid in subject_ids:
        # Placeholder for actual download logic
        # In real implementation, this would download from HCP database
        logger.log_operation("download_cifti", params={"subject": sid, "status": "skipped_demo"})
    return files


def download_hcp_data() -> Dict[str, str]:
    """Main download function."""
    paths = get_paths()
    ensure_dirs()

    # Fetch behavioral data
    df = fetch_behavioral_data()

    # Save behavioral data
    behavioral_output = os.path.join(paths["raw_dir"], "behavioral", "hcp1200_behavioral_data.csv")
    df.to_csv(behavioral_output, index=False)

    # Compute checksums
    checksum = compute_sha256(behavioral_output)

    # Save manifest
    manifest_path = os.path.join(paths["raw_dir"], "manifest.json")
    save_manifest(manifest_path, {
        "hcp1200_behavioral_data.csv": checksum
    })

    logger.log_operation("download_complete", params={"output": behavioral_output, "checksum": checksum})
    return {"behavioral": behavioral_output, "checksum": checksum}


def main() -> int:
    """Main entry point."""
    try:
        download_hcp_data()
        return 0
    except Exception as e:
        logger.log_operation("download_failed", params={"error": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
