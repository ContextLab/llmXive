"""
Download the MoleculeNet Lipophilicity dataset (raw SMILES + logP) and
register its SHA-256 checksum.

This script implements task T001a. It uses the verified scikit-fingerprints
loader to obtain the canonical Lipophilicity dataset, saves it to
data/raw/lipophilicity.csv, and updates the checksum manifest.
"""

import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
from skfp.datasets.moleculenet import load_lipophilicity
from llmxive_toolkit import paths, get_logger

# Setup logger
log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA-256 hash of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def read_checksums(path: Path) -> Dict[str, str]:
    """
    Parse a checksums.txt file into a {relative_path: hash} dict.
    Supports the canonical <hash>  <path> format.
    """
    checksums = {}
    if not path.is_file():
        return checksums
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "  " in line:
                h, p = line.split("  ", 1)
                checksums[p.strip()] = h.strip()
            elif ":" in line:
                p, h = line.split(":", 1)
                checksums[p.strip()] = h.strip()
    return checksums

def write_checksums(path: Path, checksums: Dict[str, str]) -> None:
    """Write checksums to path using the canonical two-space format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for rel_path, h in sorted(checksums.items()):
            f.write(f"{h}  {rel_path}\n")

def main() -> None:
    # 1. Define paths
    raw_csv_path = paths.data("raw", "lipophilicity.csv")
    checksum_path = paths.path("data", "checksums.txt")

    log.info("Downloading Lipophilicity dataset using scikit-fingerprints...")
    
    try:
        # Use the VERIFIED REAL DATA SOURCE recipe
        X, y = load_lipophilicity()
        
        # Create DataFrame
        # The schema (T001) requires 'logP', while skfp returns target as 'exp'
        df = pd.DataFrame({"smiles": X, "logP": y})
        
        log.info(f"Successfully loaded {len(df)} records.")
        
        # Save to CSV
        raw_csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw_csv_path, index=False)
        log.info(f"Wrote raw dataset to {raw_csv_path}")
        
    except Exception as e:
        log.error(f"Failed to obtain dataset: {e}")
        sys.exit(1)

    # 2. Compute and record checksum
    checksum = compute_sha256(raw_csv_path)
    rel_path = raw_csv_path.as_posix()
    log.info(f"Computed SHA-256 checksum: {checksum}")

    checksums = read_checksums(checksum_path)
    checksums[rel_path] = checksum
    write_checksums(checksum_path, checksums)
    log.info(f"Updated checksum manifest at {checksum_path}")

    log.info("Task T001a completed successfully.")

if __name__ == "__main__":
    main()