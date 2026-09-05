"""
Task T040a: ATOMIC DATA HYGIENE & GRID DEFINITION for User Story 2.

This script defines the parameter grid (N, theta, seeds), generates the
corresponding raw Wigner matrix instances, saves them to disk, and
computes SHA-256 checksums. It ensures atomic data hygiene as per
Constitution Principle III.

Grid Definition:
- N: [500, 1000, 2000] (spanning the relevant regime)
- theta: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
- seeds: [42, 123, 456]
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Project-relative imports
# We assume this script is run from the project root or code/ directory.
# Adjust sys.path if necessary to import generators.wigner
try:
    from generators.wigner import generate_wigner_matrix
except ImportError:
    # Fallback for execution context where 'code' is not in sys.path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from generators.wigner import generate_wigner_matrix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T040a_SweepHygiene")

# Define the Parameter Grid
# N values to span the regime (low, mid, high relative to BBP transition visibility)
N_VALUES = [500, 1000, 2000]
# Theta values to cover the transition region (BBP threshold is 1.0, so we go wide)
THETA_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
# Seeds for reproducibility
SEED_VALUES = [42, 123, 456]

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum_manifest(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the checksum manifest to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "T040a",
        "grid_definition": {
            "N": N_VALUES,
            "theta": THETA_VALUES,
            "seeds": SEED_VALUES
        },
        "files": checksums
    }
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Checksum manifest saved to {output_path}")

def run_sweep_generation() -> List[Dict[str, Any]]:
    """
    Iterate over the grid, generate matrices, save them, and compute checksums.
    Returns a list of checksum records.
    """
    checksums = []
    raw_sweep_dir = Path("data/raw/sweep")
    raw_sweep_dir.mkdir(parents=True, exist_ok=True)

    total_configs = len(N_VALUES) * len(THETA_VALUES) * len(SEED_VALUES)
    logger.info(f"Starting sweep generation for {total_configs} configurations.")

    count = 0
    for n in N_VALUES:
        for theta in THETA_VALUES:
            for seed in SEED_VALUES:
                count += 1
                logger.info(f"Processing ({count}/{total_configs}): N={n}, theta={theta}, seed={seed}")

                # 1. Generate Raw Matrix
                # We use the Wigner generator. Note: The task requires generating
                # the base Wigner matrix. The perturbation (theta) is a parameter
                # associated with this run configuration, even if the perturbation
                # is added in a later step (T020). We store the base matrix here.
                try:
                    matrix = generate_wigner_matrix(n, seed=seed)
                except Exception as e:
                    logger.error(f"Failed to generate matrix for N={n}, seed={seed}: {e}")
                    continue

                # 2. Save Matrix to Disk
                filename = f"matrix_N{n}_theta{theta}_seed{seed}.npy"
                file_path = raw_sweep_dir / filename
                np.save(file_path, matrix)

                if not file_path.exists():
                    logger.error(f"Failed to save matrix to {file_path}")
                    continue

                # 3. Compute Checksum
                checksum = compute_file_sha256(file_path)

                # 4. Record
                record = {
                    "filename": filename,
                    "path": str(file_path),
                    "n": n,
                    "theta": theta,
                    "seed": seed,
                    "sha256": checksum,
                    "size_bytes": file_path.stat().st_size
                }
                checksums.append(record)
                logger.info(f"Saved and checksummed: {filename} (SHA256: {checksum[:16]}...)")

    return checksums

def main():
    parser = argparse.ArgumentParser(description="Task T040a: Generate and checksum sweep matrices.")
    parser.add_argument("--output", type=str, default="state/checksums_sweep.json",
                        help="Path to save the checksum manifest.")
    args = parser.parse_args()

    output_path = Path(args.output)

    logger.info("Starting Task T040a: Atomic Data Hygiene & Grid Definition")

    try:
        checksums = run_sweep_generation()
        if not checksums:
            logger.error("No matrices were generated. Aborting.")
            sys.exit(1)

        save_checksum_manifest(checksums, output_path)
        logger.info("Task T040a completed successfully.")
    except Exception as e:
        logger.critical(f"Task T040a failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()