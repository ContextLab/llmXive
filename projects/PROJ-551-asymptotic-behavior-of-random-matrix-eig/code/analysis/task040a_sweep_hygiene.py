"""
Task T040a: Atomic Data Hygiene & Grid Definition for Parameter Sweep.

This module defines the explicit parameter grid for the Monte Carlo sweep,
generates raw Wigner matrix instances for each configuration, saves them to disk,
computes SHA-256 checksums, and records the manifest in state/checksums_sweep.json.

Dependencies:
- T005: utils/checksum.py (for checksum utilities)
- T012: generators/wigner.py (for matrix generation)
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

# Project-relative imports
# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from generators.wigner import generate_wigner_matrix
from utils.config import ensure_directories, get_project_paths


# Define the explicit parameter grid as per task description
# N: low, medium, high ranges. Using specific values for reproducibility.
# Based on typical RMT studies and memory constraints (N=2000 is max safe).
N_VALUES = [500, 1000, 2000]

# Theta: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
THETA_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

# Seeds: [42, 123, 456, 789] (deterministic list)
SEED_VALUES = [42, 123, 456, 789]


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_checksum_manifest(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the checksum manifest to a JSON file.

    Args:
        checksums: List of checksum records.
        output_path: Path to the output JSON file.
    """
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "T040a",
        "grid_params": {
            "N": N_VALUES,
            "theta": THETA_VALUES,
            "seeds": SEED_VALUES
        },
        "total_entries": len(checksums),
        "checksums": checksums
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logging.info(f"Checksum manifest saved to {output_path}")


def run_sweep_generation(output_base: Path) -> List[Dict[str, Any]]:
    """
    Generate raw Wigner matrices for the defined parameter grid,
    save them, compute checksums, and return the manifest records.

    Args:
        output_base: Base directory for raw data (data/raw/sweep).

    Returns:
        List of checksum records.
    """
    checksums = []
    total_configs = len(N_VALUES) * len(THETA_VALUES) * len(SEED_VALUES)
    logging.info(f"Starting sweep generation for {total_configs} configurations.")

    for N in N_VALUES:
        for theta in THETA_VALUES:
            for seed in SEED_VALUES:
                # Define filename
                filename = f"matrix_N{N}_theta{theta:.1f}_seed{seed}.npy"
                file_path = output_base / filename

                # Generate matrix
                # Note: generate_wigner_matrix takes N and seed.
                # We pass theta as a parameter to the generator if needed,
                # but typically the Wigner matrix itself is unperturbed here.
                # The perturbation is added in downstream tasks (T020a).
                # However, the task description says "generate raw matrix instances".
                # We generate the base Wigner matrix.
                try:
                    matrix = generate_wigner_matrix(N, seed=seed)
                    
                    # Save matrix
                    import numpy as np
                    np.save(file_path, matrix)
                    
                    # Compute checksum
                    checksum = compute_file_sha256(file_path)
                    
                    # Record
                    record = {
                        "filename": filename,
                        "path": str(file_path),
                        "N": N,
                        "theta": theta,
                        "seed": seed,
                        "checksum_sha256": checksum,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    checksums.append(record)
                    
                    logging.debug(f"Generated: {filename} (SHA256: {checksum[:16]}...)")
                    
                except Exception as e:
                    logging.error(f"Failed to generate/save matrix for N={N}, theta={theta}, seed={seed}: {e}")
                    raise

    return checksums


def main():
    """
    Main entry point for Task T040a.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Get project paths
    project_root, data_raw, state_dir = get_project_paths()
    
    # Define output directories
    sweep_raw_dir = data_raw / "sweep"
    checksum_output = state_dir / "checksums_sweep.json"

    # Ensure directories exist
    ensure_directories([sweep_raw_dir, state_dir])

    logging.info(f"Output directory: {sweep_raw_dir}")
    logging.info(f"Checksum output: {checksum_output}")

    # Run generation
    checksums = run_sweep_generation(sweep_raw_dir)

    # Save manifest
    save_checksum_manifest(checksums, checksum_output)

    logging.info(f"T040a completed. Generated {len(checksums)} matrices.")


if __name__ == "__main__":
    main()