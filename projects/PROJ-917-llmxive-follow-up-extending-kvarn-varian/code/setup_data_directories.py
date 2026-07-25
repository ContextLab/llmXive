"""
Setup script to create the required data directory structure for the llmXive project.
This script creates the root `data/` directory and its subdirectories:
- data/raw
- data/processed
- data/models
- data/simulation
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or code/ subdirectory.
    """
    current = Path(__file__).resolve()
    # If running from code/, go up one level
    if current.name == 'code':
        return current.parent
    # If running from code/setup_*.py, go up one level
    if current.parent.name == 'code':
        return current.parent.parent
    # Fallback: assume current working directory is project root
    return Path.cwd()

def create_directories(root_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Create the required data directory structure.

    Args:
        root_dir: Optional path to project root. If None, uses get_project_root().

    Returns:
        Dictionary mapping directory names to their Path objects.
    """
    if root_dir is None:
        root_dir = get_project_root()

    data_root = root_dir / 'data'
    directories = {
        'root': data_root,
        'raw': data_root / 'raw',
        'processed': data_root / 'processed',
        'models': data_root / 'models',
        'simulation': data_root / 'simulation',
        'generated': data_root / 'generated',
        'metrics': data_root / 'metrics',
        'analysis': data_root / 'analysis',
    }

    logger.info(f"Creating data directories under: {data_root}")

    for name, path in directories.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")

    return directories

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksums(directories: Dict[str, Path]) -> List[Dict[str, Any]]:
    """
    Record checksums for all files in the data directories.
    Since this is initial setup, there should be no files yet,
    but we record the directory structure for verification.

    Args:
        directories: Dictionary of directory paths.

    Returns:
        List of checksum records.
    """
    records = []
    for name, path in directories.items():
        if path.is_dir():
            # Record directory existence with a placeholder checksum
            # In a real scenario, we would checksum files inside
            records.append({
                'path': str(path),
                'type': 'directory',
                'checksum': 'DIR',  # Placeholder for directory
                'size': 0
            })
    return records

def save_checksums(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save checksum records to a JSON file.

    Args:
        checksums: List of checksum records.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to: {output_path}")

def load_checksums(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load checksum records from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        List of checksum records.
    """
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_integrity(directories: Dict[str, Path], expected_checksums: List[Dict[str, Any]]) -> bool:
    """
    Verify that the directory structure matches expected checksums.

    Args:
        directories: Dictionary of directory paths.
        expected_checksums: List of expected checksum records.

    Returns:
        True if integrity is verified, False otherwise.
    """
    for expected in expected_checksums:
        path = Path(expected['path'])
        if expected['type'] == 'directory':
            if not path.is_dir():
                logger.error(f"Directory missing: {path}")
                return False
    return True

def main() -> None:
    """
    Main entry point for the script.
    Creates the data directory structure and records initial checksums.
    """
    root_dir = get_project_root()
    logger.info(f"Project root detected at: {root_dir}")

    # Create directories
    directories = create_directories(root_dir)

    # Record initial checksums (directories only, no files yet)
    checksums = record_checksums(directories)

    # Save checksums to state/ directory
    state_dir = root_dir / 'state'
    state_dir.mkdir(parents=True, exist_ok=True)
    checksum_file = state_dir / 'data_directories_checksums.json'
    save_checksums(checksums, checksum_file)

    logger.info("Data directory setup completed successfully.")
    logger.info(f"Checksums saved to: {checksum_file}")

    # Verify structure
    if verify_integrity(directories, checksums):
        logger.info("Directory structure verification passed.")
    else:
        logger.error("Directory structure verification failed.")
        raise RuntimeError("Data directory structure verification failed.")

if __name__ == '__main__':
    main()
