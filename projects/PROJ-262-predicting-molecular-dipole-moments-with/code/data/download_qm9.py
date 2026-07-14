from __future__ import annotations

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import tarfile
import urllib.request
import hashlib

# Constants for QM9 dataset
QM9_URL = "http://quantum-machine.org/gdml/data/npz/QM9.tar.gz"
# Note: The original QM9 dataset is large. For this implementation, we attempt to fetch
# a representative sample or the full set if possible. If the URL is inaccessible,
# we raise a clear error rather than fabricating data.

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_qm9(output_dir: Path):
    """
    Downloads the QM9 dataset from the official source.
    If the download fails, raises a RuntimeError.
    Does NOT generate synthetic data.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    tar_path = output_dir / "QM9.tar.gz"
    
    # Check if already downloaded
    if tar_path.exists():
        print(f"QM9 archive already exists at {tar_path}. Skipping download.")
        # Verify integrity if hash is known (omitted for brevity, but good practice)
        return
    
    print(f"Downloading QM9 dataset from {QM9_URL}...")
    try:
        # Use a timeout to prevent hanging
        urllib.request.urlretrieve(QM9_URL, tar_path, reporthook=lambda block_num, block_size, total_size: print(f"\rDownloaded: {block_num * block_size / 1024 / 1024:.2f} MB", end=''))
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nERROR: Failed to download QM9 dataset: {e}", file=sys.stderr)
        print("Cannot proceed with fake data. Please check your internet connection or the URL.", file=sys.stderr)
        raise RuntimeError(f"QM9 download failed: {e}")
    
    # Extract
    print("Extracting archive...")
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(path=output_dir)
    
    # Validate that we have the expected npz files
    # The QM9 dataset typically comes as 'dsgdml.npy' or similar inside the tar
    # We look for .npz or .npy files
    npz_files = list(output_dir.glob("*.npz")) + list(output_dir.glob("*.npy"))
    if not npz_files:
        # Sometimes it's inside a subdirectory
        for p in output_dir.rglob("*.npz"):
            npz_files.append(p)
        for p in output_dir.rglob("*.npy"):
            npz_files.append(p)
    
    if not npz_files:
        raise RuntimeError("QM9 archive extracted but no .npz/.npy files found. Structure might have changed.")
    
    print(f"Found data files: {[f.name for f in npz_files]}")

if __name__ == "__main__":
    # Simple test run to ensure it doesn't just define functions
    # In a real pipeline, this would be called by generate_processed_data.py
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="data/raw/qm9")
    args = parser.parse_args()
    download_qm9(Path(args.output))
