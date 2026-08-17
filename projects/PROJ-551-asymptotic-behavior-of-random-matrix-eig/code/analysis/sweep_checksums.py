import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

from utils.config import get_project_paths

# Configure logger
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        raise

def find_sweep_matrices(base_dir: Path) -> List[Path]:
    """Find all raw matrix instances in the sweep directory."""
    sweep_dir = base_dir / "data" / "raw" / "sweep"
    if not sweep_dir.exists():
        logger.warning(f"Sweep directory does not exist: {sweep_dir}")
        return []
    
    # Find all .npy files matching the pattern matrix_N{N}_theta{theta}_seed{seed}.npy
    matrices = list(sweep_dir.glob("matrix_N*_theta*_seed*.npy"))
    return sorted(matrices)

def checksum_sweep_matrices(output_path: Path, base_dir: Path = None) -> Dict[str, Any]:
    """Compute checksums for all raw matrix instances in the sweep directory."""
    if base_dir is None:
        base_dir = get_project_paths()["project_root"]
    
    matrices = find_sweep_matrices(Path(base_dir))
    
    if not matrices:
        logger.warning("No sweep matrices found to checksum.")
        return {"status": "empty", "count": 0, "checksums": {}}

    checksums = {}
    total_size = 0
    
    for matrix_path in matrices:
        try:
            checksum = compute_file_sha256(matrix_path)
            relative_path = str(matrix_path.relative_to(Path(base_dir)))
            checksums[relative_path] = checksum
            total_size += matrix_path.stat().st_size
            logger.info(f"Checksummed: {relative_path} -> {checksum}")
        except Exception as e:
            logger.error(f"Failed to checksum {matrix_path}: {e}")
            # Fail loudly - do not skip
            raise

    result = {
        "status": "success",
        "count": len(matrices),
        "total_size_bytes": total_size,
        "checksums": checksums,
        "algorithm": "sha256"
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Checksums written to {output_path}")
    return result

def main():
    """Main entry point for sweep checksums computation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    paths = get_project_paths()
    output_path = Path(paths["project_root"]) / "state" / "checksums_sweep.json"
    
    try:
        result = checksum_sweep_matrices(output_path, Path(paths["project_root"]))
        logger.info(f"Completed checksumming {result['count']} matrices.")
    except Exception as e:
        logger.error(f"Checksum process failed: {e}")
        raise

if __name__ == "__main__":
    main()