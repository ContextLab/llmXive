"""
Task T019: ATOMIC DATA HYGIENE
Generate raw Wigner matrix instances and immediately checksum them.
Produces data/raw/matrix_N{N}_seed{seed}.npy and updates state/checksums_raw.json.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_paths, get_seed, get_matrix_size
from generators.wigner import generate_wigner_matrix
from utils.checksum import compute_file_checksum, save_checksum_manifest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_existing_checksums(state_dir: Path) -> Dict[str, Any]:
    """Load existing checksums manifest or return empty structure."""
    checksum_file = state_dir / "checksums_raw.json"
    if checksum_file.exists():
        try:
            with open(checksum_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing checksums: {e}. Starting fresh.")
    return {"checksums": [], "metadata": {"version": "1.0", "created": None}}

def save_checksums(state_dir: Path, data: Dict[str, Any]) -> None:
    """Save checksums manifest to disk."""
    checksum_file = state_dir / "checksums_raw.json"
    with open(checksum_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Checksums saved to {checksum_file}")

def run_hygiene_capture(
    N: Optional[int] = None,
    seed: Optional[int] = None,
    output_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a single Wigner matrix, save it, compute checksum, and update manifest.
    
    Args:
        N: Matrix dimension. Defaults to config value.
        seed: Random seed. Defaults to config value.
        output_dir: Directory for raw data. Defaults to config value.
        state_dir: Directory for state/checksums. Defaults to config value.
    
    Returns:
        Dictionary containing the result of the capture operation.
    """
    # Resolve paths
    paths = get_project_paths()
    raw_dir = output_dir or paths["raw_data"]
    state_directory = state_dir or paths["state"]
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    state_directory.mkdir(parents=True, exist_ok=True)
    
    # Get parameters
    if N is None:
        N = get_matrix_size()
    if seed is None:
        seed = get_seed()
    
    logger.info(f"Generating Wigner matrix: N={N}, seed={seed}")
    
    # Generate matrix
    matrix = generate_wigner_matrix(N, seed)
    
    # Define output file path
    file_name = f"matrix_N{N}_seed{seed}.npy"
    file_path = raw_dir / file_name
    
    # Save matrix
    np.save(file_path, matrix)
    logger.info(f"Matrix saved to {file_path}")
    
    # Compute checksum
    checksum = compute_file_sha256(file_path)
    logger.info(f"Computed SHA-256: {checksum}")
    
    # Load existing manifest
    manifest = load_existing_checksums(state_directory)
    
    # Create new entry
    entry = {
        "file": file_name,
        "path": str(file_path),
        "checksum": checksum,
        "algorithm": "sha256",
        "parameters": {
            "N": N,
            "seed": seed
        },
        "timestamp": None  # Will be set by save_checksum_manifest if needed
    }
    
    # Add to manifest
    if "checksums" not in manifest:
        manifest["checksums"] = []
    manifest["checksums"].append(entry)
    
    # Update metadata timestamp
    from datetime import datetime, timezone
    manifest["metadata"]["created"] = datetime.now(timezone.utc).isoformat()
    
    # Save updated manifest
    save_checksums(state_directory, manifest)
    
    return {
        "success": True,
        "file": str(file_path),
        "checksum": checksum,
        "N": N,
        "seed": seed
    }

def main():
    """CLI entry point for Task T019."""
    parser = argparse.ArgumentParser(
        description="Task T019: Generate raw Wigner matrix and checksum."
    )
    parser.add_argument(
        "--N",
        type=int,
        default=None,
        help="Matrix dimension (default: from config)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (default: from config)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for raw data"
    )
    parser.add_argument(
        "--state-dir",
        type=str,
        default=None,
        help="Directory for state/checksums"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_hygiene_capture(
            N=args.N,
            seed=args.seed,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            state_dir=Path(args.state_dir) if args.state_dir else None
        )
        
        if result["success"]:
            logger.info(f"Task T019 completed successfully.")
            logger.info(f"  File: {result['file']}")
            logger.info(f"  Checksum: {result['checksum']}")
            sys.exit(0)
        else:
            logger.error("Task T019 failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Task T019 failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()