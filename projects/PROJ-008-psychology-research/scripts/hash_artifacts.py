"""
Artifact Hashing Utility for Constitution Principle V (Reproducibility).

This script computes cryptographic hashes (SHA-256) for all artifacts in the
project's data and code directories to ensure data integrity and reproducibility.
It generates a manifest file `data/processed/artifact_manifest.json` containing
file paths, relative paths, SHA-256 hashes, and file sizes.

Constitution Principle V: Reproducibility requires that all artifacts be
uniquely identifiable and verifiable. This utility provides that mechanism.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
HASH_ALGORITHM = "sha256"
MANIFEST_FILENAME = "artifact_manifest.json"
MANIFEST_PATH = project_root / "data" / "processed" / MANIFEST_FILENAME

# Directories to hash (relative to project root)
TARGET_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "contracts",
    "tests",
    "docs",
    "specs"
]

# Files to exclude from hashing (e.g., manifest itself, logs, large binaries)
EXCLUDE_PATTERNS = [
    MANIFEST_FILENAME,
    ".log",
    ".pyc",
    "__pycache__",
    ".DS_Store",
    "*.tmp",
    "*.bak"
]

def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash, or None if file cannot be read.
    """
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"File does not exist or is not a file: {file_path}")
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def should_exclude(file_path: Path) -> bool:
    """
    Determine if a file should be excluded from hashing.

    Args:
        file_path: Path to the file.

    Returns:
        True if the file should be excluded, False otherwise.
    """
    file_name = file_path.name
    file_suffix = file_path.suffix

    # Check against exclusion patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if file_name.endswith(pattern[1:]):
                return True
        elif pattern in file_name or pattern == file_suffix:
            return True

    # Exclude hidden files/directories
    if file_name.startswith(".") or any(p.startswith(".") for p in file_path.parts):
        return True

    return False

def hash_artifacts(target_dirs: List[str], project_root: Path) -> List[Dict[str, Any]]:
    """
    Hash all eligible files in the specified directories.

    Args:
        target_dirs: List of directory paths relative to project_root.
        project_root: Root path of the project.

    Returns:
        List of dictionaries containing file metadata and hash.
    """
    artifacts = []
    total_files = 0
    hashed_files = 0

    for dir_name in target_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            logger.warning(f"Target directory does not exist: {dir_path}")
            continue

        logger.info(f"Scanning directory: {dir_path}")
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                if should_exclude(file_path):
                    logger.debug(f"Excluding: {file_path.relative_to(project_root)}")
                    continue

                file_hash = compute_file_hash(file_path)
                if file_hash:
                    relative_path = str(file_path.relative_to(project_root))
                    file_size = file_path.stat().st_size
                    artifacts.append({
                        "path": relative_path,
                        "hash": file_hash,
                        "size_bytes": file_size,
                        "algorithm": HASH_ALGORITHM
                    })
                    hashed_files += 1
                    logger.debug(f"Hashed: {relative_path} ({file_hash[:16]}...)")

    logger.info(f"Hashed {hashed_files} of {total_files} files.")
    return artifacts

def save_manifest(artifacts: List[Dict[str, Any]], manifest_path: Path) -> bool:
    """
    Save the artifact manifest to a JSON file.

    Args:
        artifacts: List of artifact metadata dictionaries.
        manifest_path: Path to save the manifest.

    Returns:
        True if successful, False otherwise.
    """
    manifest_dir = manifest_path.parent
    if not manifest_dir.exists():
        manifest_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created manifest directory: {manifest_dir}")

    manifest_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": HASH_ALGORITHM,
        "total_artifacts": len(artifacts),
        "artifacts": artifacts
    }

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"Manifest saved to: {manifest_path}")
        return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to save manifest: {e}")
        return False

def verify_artifacts(manifest_path: Path, project_root: Path) -> bool:
    """
    Verify existing artifacts against a manifest.

    Args:
        manifest_path: Path to the manifest file.
        project_root: Root path of the project.

    Returns:
        True if all artifacts match, False otherwise.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return False

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load manifest: {e}")
        return False

    artifacts = manifest_data.get("artifacts", [])
    mismatches = []

    for artifact in artifacts:
        file_path = project_root / artifact["path"]
        expected_hash = artifact["hash"]

        if not file_path.exists():
            logger.warning(f"File missing: {artifact['path']}")
            mismatches.append({"path": artifact["path"], "status": "missing"})
            continue

        actual_hash = compute_file_hash(file_path)
        if actual_hash != expected_hash:
            logger.warning(f"Hash mismatch: {artifact['path']}")
            mismatches.append({
                "path": artifact["path"],
                "expected": expected_hash,
                "actual": actual_hash
            })

    if mismatches:
        logger.error(f"Verification failed: {len(mismatches)} mismatches found.")
        return False

    logger.info("Verification successful: All artifacts match.")
    return True

def main():
    """
    Main entry point for the artifact hashing utility.

    Usage:
        python scripts/hash_artifacts.py [--verify]

    If --verify is provided, verifies artifacts against the manifest.
    Otherwise, generates a new manifest.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Artifact Hashing Utility")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify artifacts against existing manifest"
    )
    args = parser.parse_args()

    if args.verify:
        success = verify_artifacts(MANIFEST_PATH, project_root)
        sys.exit(0 if success else 1)
    else:
        logger.info("Starting artifact hashing...")
        artifacts = hash_artifacts(TARGET_DIRS, project_root)
        success = save_manifest(artifacts, MANIFEST_PATH)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
