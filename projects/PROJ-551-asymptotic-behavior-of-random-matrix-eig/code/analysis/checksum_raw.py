import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

from utils.config import get_project_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def find_raw_matrices(raw_data_dir: Path) -> List[Path]:
    """
    Find all raw matrix files in the specified directory.

    Args:
        raw_data_dir: Path to the raw data directory.

    Returns:
        List of Path objects for all .npy files found.
    """
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return []

    # Find all .npy files in the directory (non-recursive for raw matrices)
    matrix_files = list(raw_data_dir.glob("matrix_*.npy"))
    
    # Also check subdirectories if they exist (e.g., for sweep data)
    for subdir in raw_data_dir.iterdir():
        if subdir.is_dir():
            matrix_files.extend(subdir.glob("matrix_*.npy"))
    
    logger.info(f"Found {len(matrix_files)} raw matrix files in {raw_data_dir}")
    return matrix_files

def checksum_raw_matrices(matrix_files: List[Path], output_path: Path) -> Dict[str, Any]:
    """
    Compute checksums for a list of matrix files and save to a JSON manifest.

    Args:
        matrix_files: List of paths to matrix files.
        output_path: Path where the checksum manifest will be saved.

    Returns:
        Dictionary containing the checksum manifest.
    """
    checksums = {}
    failed_files = []

    for file_path in matrix_files:
        try:
            checksum = compute_file_sha256(file_path)
            checksums[str(file_path)] = {
                "sha256": checksum,
                "size_bytes": file_path.stat().st_size,
                "status": "verified"
            }
            logger.info(f"Checksummed: {file_path.name} -> {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            failed_files.append(str(file_path))
            checksums[str(file_path)] = {
                "status": "failed",
                "error": str(e)
            }

    manifest = {
        "generated_at": str(Path(output_path).parent),
        "total_files": len(matrix_files),
        "verified_count": len(checksums) - len(failed_files),
        "failed_count": len(failed_files),
        "checksums": checksums
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Checksum manifest saved to {output_path}")
    
    if failed_files:
        logger.warning(f"Failed to checksum {len(failed_files)} files: {failed_files}")

    return manifest

def main():
    """
    Main entry point for checksumming raw matrix instances.
    """
    paths = get_project_paths()
    raw_data_dir = paths['data_raw']
    state_dir = paths['state']
    output_path = state_dir / "checksums_raw.json"

    logger.info(f"Starting raw matrix checksum process...")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Output manifest: {output_path}")

    # Find all raw matrix files
    matrix_files = find_raw_matrices(raw_data_dir)

    if not matrix_files:
        logger.warning("No raw matrix files found. Creating empty manifest.")
        manifest = {
            "generated_at": str(raw_data_dir),
            "total_files": 0,
            "verified_count": 0,
            "failed_count": 0,
            "checksums": {}
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        return

    # Compute checksums and save manifest
    manifest = checksum_raw_matrices(matrix_files, output_path)

    # Report results
    logger.info(f"Completed. Verified: {manifest['verified_count']}, Failed: {manifest['failed_count']}")
    
    if manifest['failed_count'] > 0:
        raise RuntimeError(f"Checksum failed for {manifest['failed_count']} files.")

if __name__ == "__main__":
    main()