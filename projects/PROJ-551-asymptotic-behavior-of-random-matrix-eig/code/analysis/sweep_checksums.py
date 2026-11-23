import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def find_sweep_matrices(base_dir: Path) -> List[Path]:
    """
    Find all raw matrix instances in the sweep directory.

    Args:
        base_dir: Base directory containing the sweep subdirectory.

    Returns:
        List of paths to .npy matrix files.
    """
    sweep_dir = base_dir / "data" / "raw" / "sweep"
    if not sweep_dir.exists():
        logger.warning(f"Sweep directory does not exist: {sweep_dir}")
        return []

    matrix_files = list(sweep_dir.glob("matrix_N*_theta*_seed*.npy"))
    logger.info(f"Found {len(matrix_files)} matrix files in {sweep_dir}")
    return matrix_files


def checksum_sweep_matrices(base_dir: Path, output_path: Path) -> Dict[str, Any]:
    """
    Compute SHA-256 checksums for all raw matrix instances in the sweep directory
    and record them in a JSON manifest.

    Args:
        base_dir: Project root directory.
        output_path: Path to write the checksum manifest JSON.

    Returns:
        Dictionary containing the checksum manifest data.

    Raises:
        FileNotFoundError: If no matrix files are found.
        IOError: If files cannot be read or manifest cannot be written.
    """
    matrix_files = find_sweep_matrices(base_dir)
    
    if not matrix_files:
        raise FileNotFoundError(
            "No raw matrix instances found in data/raw/sweep/. "
            "Ensure T040a has been executed to generate the sweep matrices."
        )

    checksums: Dict[str, str] = {}
    total_size = 0

    for file_path in matrix_files:
        try:
            checksum = compute_file_sha256(file_path)
            # Store relative path from project root for portability
            rel_path = str(file_path.relative_to(base_dir))
            checksums[rel_path] = checksum
            total_size += file_path.stat().st_size
            logger.info(f"Checksummed: {rel_path} -> {checksum[:16]}...")
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            raise

    manifest = {
        "algorithm": "SHA-256",
        "total_files": len(matrix_files),
        "total_size_bytes": total_size,
        "checksums": checksums,
        "generated_at": str(Path(output_path).parent), # Just a placeholder context
        "status": "complete"
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to: {output_path}")
    except IOError as e:
        raise IOError(f"Failed to write checksum manifest to {output_path}: {e}")

    return manifest


def main() -> int:
    """
    Entry point for the sweep checksums script.
    """
    # Determine project root
    # Assuming script is run from code/analysis or project root
    # We look for 'data' directory relative to script location or cwd
    current_dir = Path.cwd()
    
    # Check if we are in code/analysis
    if (current_dir / "data").exists():
        project_root = current_dir
    elif (current_dir.parent / "data").exists():
        project_root = current_dir.parent
    else:
        # Fallback: assume current dir is root
        project_root = current_dir
        logger.warning(f"Could not auto-detect project root, using {project_root}")

    output_file = project_root / "state" / "checksums_sweep.json"

    try:
        logger.info(f"Starting sweep checksum generation for project root: {project_root}")
        manifest = checksum_sweep_matrices(project_root, output_file)
        logger.info(f"Successfully checksummed {manifest['total_files']} files.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing data: {e}")
        return 1
    except IOError as e:
        logger.error(f"I/O Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
