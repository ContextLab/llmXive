"""
Data download utilities for OpenNeuro datasets.

Handles checksum verification and partial downloads.
"""

import os
import hashlib
import logging
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

def calculate_md5(filepath):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_checksum(filepath, expected_md5):
    """Verify file checksum against expected value."""
    if not os.path.exists(filepath):
        return False
    actual_md5 = calculate_md5(filepath)
    return actual_md5 == expected_md5

def download_openneuro_dataset(dataset_id, output_dir, subjects=None, session=None):
    """
    Download a subset of an OpenNeuro dataset using openneuro-cli.
    
    Args:
        dataset_id: OpenNeuro dataset ID (e.g., 'ds000234').
        output_dir: Local directory to store downloaded data.
        subjects: List of subject IDs to download (e.g., ['sub-01']).
        session: Optional session ID.
    
    Returns:
        Path to the downloaded directory.
    """
    output_path = Path(output_dir) / dataset_id
    output_path.mkdir(parents=True, exist_ok=True)
    
    cmd = ["openneuro", "download", "--dataset", dataset_id, "--output-dir", str(output_path)]
    
    if subjects:
        for sub in subjects:
            cmd.extend(["--subject", sub])
    
    if session:
        cmd.extend(["--session", session])
    
    # Add --overwrite to handle partial downloads
    cmd.append("--overwrite")
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Download successful: {result.stdout}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed: {e.stderr}")
        raise RuntimeError(f"OpenNeuro download failed: {e.stderr}")
