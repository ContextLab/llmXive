"""
Task T019: ATOMIC DATA HYGIENE for User Story 1.

Generates a raw Wigner matrix instance and immediately checksums it.
Produces:
  1. data/raw/matrix_N{N}_seed{seed}.npy
  2. state/checksums_raw.json (updated atomically)
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

import numpy as np

# Adjust import path to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.wigner import generate_wigner_matrix
from utils.config import get_project_paths, ensure_directories, get_seed, get_matrix_size

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_existing_checksums(state_path: Path) -> Dict[str, Any]:
    """Load existing checksums manifest or return empty structure."""
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing checksums file: {e}. Starting fresh.")
            return {"checksums": [], "metadata": {}}
    return {"checksums": [], "metadata": {}}


def save_checksums(state_path: Path, data: Dict[str, Any]) -> None:
    """Save checksums manifest atomically."""
    # Write to temp file first, then rename for atomicity
    temp_path = state_path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, state_path)
    logger.info(f"Checksums saved to {state_path}")


def run_hygiene_capture(
    N: Optional[int] = None,
    seed: Optional[int] = None,
    raw_data_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate raw Wigner matrix and checksum it atomically.

    Args:
        N: Matrix dimension. Defaults to config.
        seed: Random seed. Defaults to config.
        raw_data_dir: Directory for raw data. Defaults to config.
        state_dir: Directory for state/checksums. Defaults to config.

    Returns:
        Dictionary with generation details and checksum.
    """
    # Get paths and config
    paths = get_project_paths()
    if raw_data_dir is None:
        raw_data_dir = paths['data_raw']
    if state_dir is None:
        state_dir = paths['state']

    if N is None:
        N = get_matrix_size()
    if seed is None:
        seed = get_seed()

    # Ensure directories exist
    ensure_directories()

    # Define output paths
    matrix_filename = f"matrix_N{N}_seed{seed}.npy"
    matrix_path = raw_data_dir / matrix_filename
    checksum_path = state_dir / "checksums_raw.json"

    logger.info(f"Generating Wigner matrix: N={N}, seed={seed}")
    logger.info(f"Output path: {matrix_path}")

    # Generate the matrix
    # Using the API from generators.wigner
    matrix = generate_wigner_matrix(N, seed=seed)

    # Save the matrix
    logger.info("Saving matrix to disk...")
    np.save(str(matrix_path), matrix)

    if not matrix_path.exists():
        raise RuntimeError(f"Failed to save matrix to {matrix_path}")

    # Compute checksum
    logger.info("Computing SHA-256 checksum...")
    checksum = compute_file_sha256(matrix_path)

    # Prepare record
    record = {
        "file": matrix_filename,
        "path": str(matrix_path),
        "checksum": checksum,
        "algorithm": "sha256",
        "parameters": {
            "N": N,
            "seed": seed,
            "matrix_type": "wigner_dense"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Load existing checksums and append
    existing = load_existing_checksums(checksum_path)
    existing["checksums"].append(record)
    existing["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    existing["metadata"]["total_entries"] = len(existing["checksums"])

    # Save atomically
    save_checksums(checksum_path, existing)

    logger.info(f"SUCCESS: Matrix saved and checksummed.")
    logger.info(f"  File: {matrix_path}")
    logger.info(f"  Checksum: {checksum}")

    return record


def main():
    """CLI entry point for T019."""
    parser = argparse.ArgumentParser(
        description="Task T019: Generate raw Wigner matrix and checksum it."
    )
    parser.add_argument(
        "--N",
        type=int,
        default=None,
        help="Matrix dimension (overrides config)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (overrides config)"
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Raw data directory (overrides config)"
    )
    parser.add_argument(
        "--state-dir",
        type=str,
        default=None,
        help="State directory (overrides config)"
    )

    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    state_dir = Path(args.state_dir) if args.state_dir else None

    try:
        result = run_hygiene_capture(
            N=args.N,
            seed=args.seed,
            raw_data_dir=raw_dir,
            state_dir=state_dir
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Task T019 failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())