"""
Data Directory Initialization Script for llmXive Project.

This script initializes the required directory structure for the project's data artifacts.
It creates the following hierarchy under the project root:
- data/raw: For raw, unprocessed datasets
- data/processed: For cleaned and transformed data
- data/results: For simulation outputs and analysis results
- data/models: For trained model weights and checkpoints

Verification:
- Ensures all directories exist after execution.
- Logs success or failure.
"""

import os
import sys
import logging
from pathlib import Path
import hashlib
import json
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determines the project root directory.
    Assumes the script is run from the project root or one level deep.
    """
    current_path = Path(__file__).resolve()
    # If running from code/, go up one level
    if current_path.name == 'setup_data_directories.py':
        return current_path.parent.parent
    return current_path.parent

def create_directories(base_path: Path) -> Dict[str, bool]:
    """
    Creates the required data directory structure.

    Args:
        base_path: The root path where 'data' will be created.

    Returns:
        A dictionary mapping directory names to their creation status (True/False).
    """
    data_root = base_path / "data"
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results",
        data_root / "models"
    ]

    results = {}
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            results[str(dir_path.relative_to(base_path))] = True
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            results[str(dir_path.relative_to(base_path))] = False
            logger.error(f"Failed to create directory {dir_path}: {e}")

    return results

def compute_file_checksum(file_path: Path) -> Optional[str]:
    """
    Computes the SHA-256 checksum of a file.
    """
    if not file_path.exists():
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return None

def record_checksums(base_path: Path, checksums: Dict[str, str]) -> None:
    """
    Records directory checksums (placeholder for directory integrity).
    Since directories themselves don't have a single hash, we record the structure.
    """
    checksum_file = base_path / "data" / ".structure_checksums.json"
    try:
        with open(checksum_file, "w") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Recorded structure checksums to {checksum_file}")
    except Exception as e:
        logger.error(f"Failed to record checksums: {e}")

def save_checksums(base_path: Path, checksums: Dict[str, str]) -> None:
    """Alias for record_checksums."""
    record_checksums(base_path, checksums)

def load_checksums(base_path: Path) -> Dict[str, str]:
    """
    Loads previously recorded checksums.
    """
    checksum_file = base_path / "data" / ".structure_checksums.json"
    if checksum_file.exists():
        try:
            with open(checksum_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def verify_integrity(base_path: Path, expected_dirs: List[str]) -> bool:
    """
    Verifies that the expected directories exist.

    Args:
        base_path: The project root.
        expected_dirs: List of relative directory paths to check.

    Returns:
        True if all directories exist, False otherwise.
    """
    all_exist = True
    for rel_dir in expected_dirs:
        full_path = base_path / rel_dir
        if not full_path.is_dir():
            logger.error(f"Missing expected directory: {full_path}")
            all_exist = False
        else:
            logger.info(f"Verified directory exists: {full_path}")
    return all_integrity

def main() -> int:
    """
    Main entry point for the directory initialization script.
    """
    project_root = get_project_root()
    logger.info(f"Project root detected at: {project_root}")

    # Define expected directories relative to project root
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/models"
    ]

    # Create directories
    creation_results = create_directories(project_root)

    if all(creation_results.values()):
        logger.info("All data directories created successfully.")

        # Record structure (simplified checksum logic for directories)
        structure_record = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "directories": list(creation_results.keys())
        }
        record_checksums(project_root, structure_record)

        # Verify integrity
        if verify_integrity(project_root, expected_dirs):
            logger.info("Verification passed: All required directories exist.")
            return 0
        else:
            logger.error("Verification failed: Some directories are missing.")
            return 1
    else:
        logger.error("Failed to create one or more directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
