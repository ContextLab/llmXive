"""
Task T019: Atomic Data Hygiene for Wigner Matrix Generation.

Generates a raw Wigner matrix instance, saves it to disk, computes its SHA-256
checksum, and registers the checksum in the unified metadata registry.

This task ensures that raw data is checksummed immediately upon generation,
satisfying Constitution Principle III (Data Hygiene).
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generators.wigner import generate_wigner_matrix
from utils.config import get_project_paths

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(registry_path: Path) -> Dict[str, Any]:
    """Load the existing metadata registry if it exists."""
    if registry_path.exists():
        with open(registry_path, "r") as f:
            return json.load(f)
    return {"entries": []}

def save_checksums(registry_path: Path, data: Dict[str, Any]) -> None:
    """Save the updated metadata registry."""
    with open(registry_path, "w") as f:
        json.dump(data, f, indent=2)

def run_hygiene_capture(
    n: int,
    seed: int,
    output_dir: Path,
    registry_path: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Generate a Wigner matrix, save it, compute checksum, and register.

    Returns the metadata record created.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = f"matrix_N{n}_seed{seed}.npy"
    file_path = output_dir / filename

    logger.info(f"Generating Wigner matrix (N={n}, seed={seed})...")
    matrix = generate_wigner_matrix(n, seed=seed)

    logger.info(f"Saving matrix to {file_path}...")
    import numpy as np
    np.save(file_path, matrix)

    logger.info(f"Computing SHA-256 checksum for {file_path}...")
    checksum = compute_file_sha256(file_path)

    # Create metadata record
    metadata_record = {
        "run_id": f"t019_N{n}_seed{seed}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "n": n,
            "seed": seed,
            "type": "wigner_matrix"
        },
        "file_path": str(file_path.relative_to(PROJECT_ROOT)),
        "checksum": {
            "algorithm": "sha256",
            "hash": checksum
        },
        "status": "completed"
    }

    # Load existing registry and append
    registry = load_existing_checksums(registry_path)
    registry["entries"].append(metadata_record)
    save_checksums(registry_path, registry)

    logger.info(f"Checksum registered in {registry_path}")
    logger.info(f"Checksum: {checksum}")

    return metadata_record

def main():
    """Main entry point for Task T019."""
    parser = argparse.ArgumentParser(
        description="Task T019: Generate Wigner matrix and checksum it."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for matrix generation (default: 42)"
    )
    parser.add_argument(
        "--N",
        type=int,
        default=1000,
        help="Dimension of the Wigner matrix (default: 1000)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save the matrix (default: data/raw)"
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        default=None,
        help="Path to metadata registry (default: state/metadata_registry.json)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("task019_hygiene")

    # Resolve paths
    project_paths = get_project_paths()
    output_dir = args.output_dir or project_paths["data_raw"]
    registry_path = args.registry_path or project_paths["state"] / "metadata_registry.json"

    logger.info(f"Task T019 starting: N={args.N}, seed={args.seed}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Registry path: {registry_path}")

    try:
        result = run_hygiene_capture(
            n=args.N,
            seed=args.seed,
            output_dir=output_dir,
            registry_path=registry_path,
            logger=logger
        )
        logger.info(f"Task T019 completed successfully. Run ID: {result['run_id']}")
        return 0
    except Exception as e:
        logger.error(f"Task T019 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
