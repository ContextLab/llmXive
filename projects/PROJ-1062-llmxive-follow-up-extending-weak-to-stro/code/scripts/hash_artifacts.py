"""
Hash Artifacts Script for llmXive Project

Generates SHA-256 hashes for all data and model artifacts in the project
to ensure integrity and reproducibility per Constitution Principle V.

This script scans the data/, data/raw/, data/processed/, data/results/,
and model checkpoint directories (if any) and generates a manifest file
with SHA-256 hashes for all files.
"""

import hashlib
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "data" / "results",
    PROJECT_ROOT / "data" / "figures",
]
OUTPUT_FILE = PROJECT_ROOT / "data" / "artifacts_manifest.json"

# Files to exclude from hashing
EXCLUDE_PATTERNS = [
    ".gitkeep",
    ".DS_Store",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.log",
    ".lock",
]

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise

def should_exclude(file_path: Path) -> bool:
    """
    Check if a file should be excluded from hashing.

    Args:
        file_path: Path to the file

    Returns:
        True if file should be excluded, False otherwise
    """
    file_name = file_path.name
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            # Handle extension patterns
            if file_name.endswith(pattern[1:]):
                return True
        else:
            if file_name == pattern:
                return True
    return False

def scan_directory(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for files to hash.

    Args:
        directory: Directory to scan

    Returns:
        List of file paths to hash
    """
    files_to_hash = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return files_to_hash

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            if not should_exclude(file_path):
                files_to_hash.append(file_path)

    return files_to_hash

def generate_manifest() -> Dict[str, Any]:
    """
    Generate a manifest of all artifacts with their SHA-256 hashes.

    Returns:
        Dictionary containing the manifest data
    """
    manifest = {
        "version": "1.0",
        "generated_at": None,  # Will be set when saving
        "project_root": str(PROJECT_ROOT),
        "artifacts": []
    }

    all_files = []
    for data_dir in DATA_DIRS:
        files = scan_directory(data_dir)
        all_files.extend(files)

    if not all_files:
        logger.warning("No artifacts found to hash. Ensure data directories are populated.")
        return manifest

    logger.info(f"Found {len(all_files)} artifacts to hash")

    for file_path in sorted(all_files):
        try:
            file_hash = compute_sha256(file_path)
            relative_path = file_path.relative_to(PROJECT_ROOT)
            file_size = file_path.stat().st_size
            file_type = file_path.suffix or "no_extension"

            artifact_entry = {
                "path": str(relative_path),
                "sha256": file_hash,
                "size_bytes": file_size,
                "type": file_type,
                "directory": str(file_path.parent.relative_to(PROJECT_ROOT))
            }
            manifest["artifacts"].append(artifact_entry)
            logger.info(f"Hashed: {relative_path} ({file_hash[:16]}...)")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            # Continue with other files even if one fails

    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Save the manifest to a JSON file.

    Args:
        manifest: Manifest dictionary
        output_path: Path to save the manifest
    """
    import datetime
    manifest["generated_at"] = datetime.datetime.utcnow().isoformat() + "Z"

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Manifest saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")
        raise

def verify_artifacts(manifest_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verify existing artifacts against a manifest.

    Args:
        manifest_path: Path to the manifest file (defaults to OUTPUT_FILE)

    Returns:
        Tuple of (all_valid, list_of_failed_files)
    """
    if manifest_path is None:
        manifest_path = OUTPUT_FILE

    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return False, ["Manifest not found"]

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return False, [f"Failed to load manifest: {e}"]

    failed_files = []

    for artifact in manifest.get("artifacts", []):
        file_path = PROJECT_ROOT / artifact["path"]
        expected_hash = artifact["sha256"]

        if not file_path.exists():
            logger.warning(f"File missing: {file_path}")
            failed_files.append(f"Missing: {artifact['path']}")
            continue

        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {file_path}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Actual:   {actual_hash}")
                failed_files.append(f"Hash mismatch: {artifact['path']}")
            else:
                logger.info(f"Verified: {artifact['path']}")
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            failed_files.append(f"Verification error: {artifact['path']}")

    return len(failed_files) == 0, failed_files

def main() -> int:
    """
    Main entry point for the hash artifacts script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting artifact hashing...")

    # Generate manifest
    manifest = generate_manifest()

    if not manifest["artifacts"]:
        logger.warning("No artifacts found. Creating empty manifest.")

    # Save manifest
    try:
        save_manifest(manifest, OUTPUT_FILE)
        logger.info("Artifact hashing completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Failed to complete artifact hashing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
