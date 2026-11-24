"""
Citation verification and data checksum recording script.

This script performs three main actions:
1. Pins random seeds for reproducibility.
2. Runs a lightweight citation verification (ensures the citations
   markdown file exists and is non‑empty).
3. Computes SHA‑256 checksums for every file under the ``data/`` directory
   (recursively) and writes a mapping of relative file paths to hashes in
   ``state/artifact_hashes.yaml``.

The script is intended to be invoked as a module:
    python -m src.verification.verify_citations

It writes its outputs to the project‑wide ``paths`` managed locations,
creating any required parent directories.
"""

import hashlib
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import yaml

# Project‑wide helpers from the llmxive toolkit
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RANDOM_SEED = 42  # Fixed seed for reproducibility

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def pin_random_seeds(seed: int = RANDOM_SEED) -> None:
    """
    Pin random seeds for the Python standard library, NumPy and any
    other common libraries that rely on a global RNG.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If other libraries (e.g., torch) are added later they can be seeded here.

def verify_citations_file() -> bool:
    """
    Very lightweight citation verification:
    - Checks that ``docs/citations.md`` exists.
    - Checks that it contains at least one non‑empty line.
    
    Returns ``True`` if the checks pass, ``False`` otherwise.
    """
    citations_path = paths.docs("citations.md")
    if not citations_path.is_file():
        return False
    try:
        with open(citations_path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
            return len(lines) > 0
    except Exception:
        return False

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file in a memory‑efficient way.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def collect_checksums(data_root: Path) -> dict:
    """
    Walk ``data_root`` recursively and compute SHA‑256 checksums for every
    file. The keys in the returned dict are POSIX‑style relative paths
    (using forward slashes) from ``data_root``.
    """
    checksums = {}
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(data_root).as_posix()
            checksums[rel_path] = compute_sha256(file_path)
    return checksums

def write_hashes_yaml(hashes: dict) -> None:
    """
    Write the ``hashes`` mapping to ``state/artifact_hashes.yaml`` using
    ``yaml.safe_dump``. The output directory is created if it does not
    already exist.
    """
    output_path = paths.state("artifact_hashes.yaml")
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(hashes, f, default_flow_style=False, sort_keys=True)

# ----------------------------------------------------------------------
# Main execution block
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for the script.
    Returns an exit code (0 on success, 1 on failure).
    """
    logger = get_logger(__name__)

    # 1. Pin seeds
    logger.info("Pinning random seeds for reproducibility (seed=%s)", RANDOM_SEED)
    pin_random_seeds(RANDOM_SEED)

    # 2. Verify citations
    logger.info("Running lightweight citation verification...")
    if not verify_citations_file():
        logger.error("Citation verification failed: 'docs/citations.md' missing or empty.")
        return 1
    logger.info("Citation verification passed.")

    # 3. Compute checksums for all files under data/
    data_root = paths.data()
    if not data_root.is_dir():
        logger.error("Data directory does not exist: %s", data_root)
        return 1

    logger.info("Computing SHA‑256 checksums for files under %s ...", data_root)
    checksums = collect_checksums(data_root)

    # 4. Write the checksum mapping to state/artifact_hashes.yaml
    logger.info("Writing artifact hashes to %s", paths.state("artifact_hashes.yaml"))
    write_hashes_yaml(checksums)

    logger.info("All tasks completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())