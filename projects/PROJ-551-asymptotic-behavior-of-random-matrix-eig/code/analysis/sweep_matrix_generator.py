"""
T040a: Atomic Data Hygiene & Grid Definition for Parameter Sweep.

This module generates raw Wigner matrices for a defined parameter grid
(N, theta, seeds), saves them as .npy files, and immediately computes
SHA-256 checksums, recording them in state/checksums_sweep.json.

It implements Constitution Principle III (Data Hygiene) by ensuring
raw data is checksummed atomically with its generation.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Project imports
# Adjust relative import based on execution context (usually run from project root)
try:
    from generators.wigner import generate_wigner_matrix
    from utils.config import ensure_directories, get_project_paths
    from utils.checksum import compute_file_checksum
except ImportError:
    # Fallback for direct script execution or different environment setup
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from generators.wigner import generate_wigner_matrix
    from utils.config import ensure_directories, get_project_paths
    from utils.checksum import compute_file_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/sweep_generation.log')
    ]
)
logger = logging.getLogger(__name__)

def generate_sweep_configs() -> List[Dict[str, Any]]:
    """
    Defines the parameter grid explicitly as per T040a requirements.

    N: [low to high values to span the relevant regime]
       Using [500, 1000, 2000] to span the regime while keeping memory tractable.
    theta: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    seeds: [42, 123, 456]

    Returns:
        List of dictionaries, each representing a unique configuration.
    """
    N_values = [500, 1000, 2000]
    theta_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    seed_values = [42, 123, 456]

    configs = []
    for N in N_values:
        for theta in theta_values:
            for seed in seed_values:
                configs.append({
                    "N": N,
                    "theta": theta,
                    "seed": seed
                })
    return configs

def save_raw_sweep_matrix(config: Dict[str, Any], output_dir: Path) -> Path:
    """
    Generates a single Wigner matrix instance for the given config,
    saves it to disk, and returns the path.

    Args:
        config: Dictionary with 'N', 'theta', 'seed'.
        output_dir: Directory to save the .npy file.

    Returns:
        Path to the saved .npy file.
    """
    N = config["N"]
    theta = config["theta"]
    seed = config["seed"]

    # Generate filename
    filename = f"matrix_N{N}_theta{theta:.1f}_seed{seed}.npy"
    file_path = output_dir / filename

    if file_path.exists():
        logger.warning(f"File {file_path} already exists. Skipping generation.")
        return file_path

    logger.info(f"Generating matrix: N={N}, theta={theta}, seed={seed}")

    # Set seed for reproducibility
    np.random.seed(seed)

    # Generate Wigner matrix
    # The generator handles the 1/sqrt(N) scaling internally as per spec
    matrix = generate_wigner_matrix(N)

    # Save to .npy
    np.save(file_path, matrix)
    logger.info(f"Saved matrix to {file_path}")

    return file_path

def compute_file_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_sweep_generation(
    configs: Optional[List[Dict[str, Any]]] = None,
    output_dir: Optional[Path] = None,
    checksum_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Executes the full sweep generation: generate matrices, save, checksum,
    and record metadata.

    Args:
        configs: List of parameter configurations. If None, uses default grid.
        output_dir: Directory for raw matrices. Defaults to data/raw/sweep.
        checksum_file: Path for checksums JSON. Defaults to state/checksums_sweep.json.

    Returns:
        Dictionary containing summary statistics and paths.
    """
    if configs is None:
        configs = generate_sweep_configs()

    if output_dir is None:
        project_paths = get_project_paths()
        output_dir = project_paths["data_raw"] / "sweep"

    if checksum_file is None:
        project_paths = get_project_paths()
        checksum_file = project_paths["state"] / "checksums_sweep.json"

    ensure_directories([output_dir, checksum_file.parent])

    logger.info(f"Starting sweep generation for {len(configs)} configurations.")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Checksum file: {checksum_file}")

    checksums = []
    start_time = datetime.now(timezone.utc)

    for i, config in enumerate(configs):
        logger.info(f"Processing config {i+1}/{len(configs)}: {config}")

        try:
            # 1. Generate and Save
            matrix_path = save_raw_sweep_matrix(config, output_dir)

            # 2. Compute Checksum (Atomic Hygiene)
            checksum = compute_file_sha256(matrix_path)

            # 3. Record Metadata
            entry = {
                "file_path": str(matrix_path.relative_to(Path.cwd())),
                "checksum": checksum,
                "config": config,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            checksums.append(entry)

            logger.info(f"Completed config {i+1}: Checksum={checksum[:16]}...")

        except Exception as e:
            logger.error(f"Failed to process config {config}: {e}", exc_info=True)
            # Fail loudly as per constraints
            raise RuntimeError(f"Failed to generate/checksum matrix for config {config}") from e

    # Save checksums manifest
    manifest = {
        "generated_at": start_time.isoformat(),
        "total_configs": len(configs),
        "checksums": checksums
    }

    with open(checksum_file, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Saved checksum manifest to {checksum_file}")
    logger.info("Sweep generation completed successfully.")

    return {
        "output_dir": str(output_dir),
        "checksum_file": str(checksum_file),
        "total_generated": len(checksums),
        "configs": configs
    }

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate raw sweep matrices with checksums (T040a)")
    parser.add_argument("--output-dir", type=str, help="Output directory for matrices")
    parser.add_argument("--checksum-file", type=str, help="Path for checksums JSON")
    parser.add_argument("--config-file", type=str, help="Optional JSON file with custom config grid")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    checksum_file = Path(args.checksum_file) if args.checksum_file else None
    configs = None

    if args.config_file:
        with open(args.config_file, "r") as f:
            configs = json.load(f)
        logger.info(f"Loaded custom configs from {args.config_file}")

    try:
        result = run_sweep_generation(
            configs=configs,
            output_dir=output_dir,
            checksum_file=checksum_file
        )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Sweep generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
