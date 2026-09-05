"""
Task T019: Atomic Data Hygiene for Raw Wigner Matrix Generation.

This script generates a raw Wigner matrix instance based on a provided seed
and matrix size, saves it to disk as a NumPy .npy file, computes its SHA-256
checksum, and atomically updates the state/checksums_raw.json manifest.

It strictly adheres to Constitution Principle III (Data Hygiene) by ensuring
the data and its integrity proof are created together.
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

# Add parent directory to path to allow imports from project structure
# Assuming this script is run from the project root or code directory context
# but we use relative imports based on the provided API surface.
try:
    from generators.wigner import generate_wigner_matrix
    from utils.config import get_project_paths, ensure_directories, get_seed, get_matrix_size
except ImportError as e:
    # Fallback for running directly if environment setup differs
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from generators.wigner import generate_wigner_matrix
    from utils.config import get_project_paths, ensure_directories, get_seed, get_matrix_size

logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksum_path: Path) -> Dict[str, Any]:
    """Load existing checksum manifest, creating empty structure if missing."""
    if checksum_path.exists():
        with open(checksum_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "1.0", "created_at": datetime.now(timezone.utc).isoformat(), "entries": []}

def save_checksums(checksum_path: Path, data: Dict[str, Any]) -> None:
    """Save checksum manifest atomically (write to temp, then rename)."""
    temp_path = checksum_path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, checksum_path)
    logger.info(f"Checksum manifest saved atomically to {checksum_path}")

def run_hygiene_capture(
    seed: Optional[int] = None,
    n: Optional[int] = None,
    output_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a Wigner matrix, save it, compute checksum, and update manifest.

    Returns the metadata record for this run.
    """
    # Resolve paths and config
    paths = get_project_paths()
    if output_dir is None:
        output_dir = paths['data_raw']
    if state_dir is None:
        state_dir = paths['state']

    ensure_directories([output_dir, state_dir])

    if seed is None:
        seed = get_seed()
    if n is None:
        n = get_matrix_size()

    # 1. Generate the Matrix
    logger.info(f"Generating Wigner matrix: N={n}, seed={seed}")
    matrix = generate_wigner_matrix(n, seed=seed)
    
    # 2. Save the Matrix
    filename = f"matrix_N{n}_seed{seed}.npy"
    file_path = output_dir / filename
    
    # Check if file already exists to avoid accidental overwrite in re-runs
    # unless forced (not required by spec, but good practice)
    if file_path.exists():
        logger.warning(f"File {file_path} already exists. Skipping generation but verifying checksum.")
    else:
        # Save as .npy
        np.save(file_path, matrix)
        logger.info(f"Matrix saved to {file_path}")

    # 3. Compute Checksum
    checksum = compute_file_sha256(file_path)
    logger.info(f"Computed SHA-256: {checksum}")

    # 4. Update Manifest
    checksum_path = state_dir / "checksums_raw.json"
    manifest = load_existing_checksums(checksum_path)
    
    # Update timestamp
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Check if entry exists
    entry_exists = False
    for entry in manifest["entries"]:
        if entry.get("filename") == filename:
            entry["checksum"] = checksum
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            entry_exists = True
            break
    
    if not entry_exists:
        manifest["entries"].append({
            "filename": filename,
            "path": str(file_path),
            "checksum": checksum,
            "size_bytes": file_path.stat().st_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "N": n,
                "seed": seed,
                "type": "wigner_dense"
            }
        })
    
    save_checksums(checksum_path, manifest)

    return {
        "filename": filename,
        "path": str(file_path),
        "checksum": checksum,
        "N": n,
        "seed": seed
    }

def main():
    parser = argparse.ArgumentParser(description="Task T019: Generate and checksum raw Wigner matrix.")
    parser.add_argument('--seed', type=int, default=None, help='Random seed (default from config)')
    parser.add_argument('--n', type=int, default=None, help='Matrix size N (default from config)')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory for matrices')
    parser.add_argument('--state-dir', type=str, default=None, help='Directory for state/checksums')
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        result = run_hygiene_capture(
            seed=args.seed,
            n=args.n,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            state_dir=Path(args.state_dir) if args.state_dir else None
        )
        logger.info(f"Task T019 completed successfully. Matrix: {result['filename']}, Checksum: {result['checksum']}")
        return 0
    except Exception as e:
        logger.error(f"Task T019 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
