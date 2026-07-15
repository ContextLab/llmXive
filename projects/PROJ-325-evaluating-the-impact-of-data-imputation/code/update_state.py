"""
update_state.py

Generates content hashes for project artifacts and updates the state manifest.
Implements Constitution Principle V: State tracking via content hashes.

This script scans specified directories for artifact files, computes their SHA-256 hashes,
and writes a manifest.yaml file to the state/ directory containing these hashes.
"""
import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
MANIFEST_PATH = STATE_DIR / "manifest.yaml"

# Directories to hash (relative to project root)
ARTIFACT_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "specs"
]

# File extensions to include
FILE_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".csv", ".md", ".txt"}

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise

def find_artifacts(base_dir: Path) -> list:
    """
    Recursively finds all relevant artifact files in a directory.
    
    Args:
        base_dir: Root directory to search.
        
    Returns:
        List of Path objects for found files.
    """
    if not base_dir.exists():
        logger.warning(f"Directory does not exist: {base_dir}")
        return []
    
    artifacts = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in FILE_EXTENSIONS:
                # Skip hidden files and common build artifacts
                if not file.startswith('.') and file not in {'__init__.pyc', 'pycache'}:
                    artifacts.append(file_path)
    return artifacts

def generate_manifest(artifact_dirs: list) -> Dict[str, Any]:
    """
    Generates a manifest dictionary containing hashes for all artifacts.
    
    Args:
        artifact_dirs: List of directory paths (relative to project root) to scan.
        
    Returns:
        Dictionary with 'artifact_hashes' key mapping relative paths to hashes.
    """
    artifact_hashes = {}
    
    for dir_name in artifact_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            logger.info(f"Skipping non-existent directory: {dir_path}")
            continue
        
        files = find_artifacts(dir_path)
        for file_path in files:
            try:
                # Store path relative to project root for portability
                relative_path = file_path.relative_to(PROJECT_ROOT)
                file_hash = compute_file_hash(file_path)
                artifact_hashes[str(relative_path)] = file_hash
                logger.debug(f"Hashed: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                raise
    
    return {
        "artifact_hashes": artifact_hashes,
        "version": "1.0",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

def update_manifest(manifest_data: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the manifest data to the YAML file, creating directories if needed.
    
    Args:
        manifest_data: Dictionary to write.
        output_path: Full path to the manifest file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Manifest updated at: {output_path}")

def main() -> int:
    """
    Main entry point for the update_state script.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting artifact state update...")
    
    try:
        manifest = generate_manifest(ARTIFACT_DIRS)
        update_manifest(manifest, MANIFEST_PATH)
        logger.info("State update completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"State update failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
