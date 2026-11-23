"""
Utilities for managing SHA256 checksums of data files.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Returns the project root directory (code/).
    Assumes this script is run from within the code/ directory or a subdirectory.
    """
    # If running as a module, __file__ is available.
    # We look for the 'code' directory which is the root.
    current = Path(__file__).resolve()
    # Traverse up until we find 'code' or root
    while current.parent != current:
        if current.name == "code":
            return current
        current = current.parent
    # Fallback: assume current working directory is code/
    return Path.cwd()

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Loads the checksum manifest from a JSON file.
    """
    with open(manifest_path, "r") as f:
        return json.load(f)

def save_checksum_manifest(manifest: Dict[str, str], manifest_path: Path):
    """
    Saves the checksum manifest to a JSON file.
    """
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

def verify_checksum(file_path: Path, expected_hash: str) -> Tuple[str, str, bool]:
    """
    Verifies a single file's checksum.
    Returns (expected_hash, actual_hash, is_valid)
    """
    actual_hash = compute_file_checksum(file_path)
    is_valid = (actual_hash == expected_hash)
    return expected_hash, actual_hash, is_valid

def verify_all_files(manifest: Dict[str, str], base_dir: Path) -> Dict[str, Tuple[str, str, bool]]:
    """
    Verifies all files listed in the manifest against their stored checksums.
    Returns a dict of {file_path: (expected, actual, is_valid)}
    """
    results = {}
    for rel_path, expected_hash in manifest.items():
        full_path = base_dir / rel_path
        if not full_path.exists():
            logger.warning(f"File not found: {full_path}")
            results[rel_path] = (expected_hash, "FILE_NOT_FOUND", False)
            continue
        
        _, actual_hash, is_valid = verify_checksum(full_path, expected_hash)
        results[rel_path] = (expected_hash, actual_hash, is_valid)
    
    return results

def update_checksum_for_file(file_path: Path, manifest: Dict[str, str]) -> Dict[str, str]:
    """
    Computes the checksum for a specific file and updates the manifest.
    """
    rel_path = str(file_path.relative_to(get_project_root()))
    h = compute_file_checksum(file_path)
    manifest[rel_path] = h
    return manifest

def main():
    """
    CLI entry point for manual checksum operations if needed.
    """
    project_root = get_project_root()
    checksum_file = project_root / "data/raw/checksums.json"
    
    if not checksum_file.exists():
        logger.info("No manifest found. Initializing empty manifest.")
        save_checksum_manifest({}, checksum_file)
    
    logger.info(f"Manifest loaded from {checksum_file}")
    manifest = load_checksum_manifest(checksum_file)
    logger.info(f"Current manifest: {manifest}")

if __name__ == "__main__":
    main()