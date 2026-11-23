from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_checksum_algorithm, get_data_root, get_processed_dir, get_analysis_dir, get_raw_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MANIFEST_PATH = Path("data/manifest.json")

def setup_logging() -> None:
    """Configure logging for the checksum module."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def compute_all_artifact_checksums(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    analysis_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Compute checksums for all artifacts in the data directories.

    Args:
        raw_dir: Path to raw data directory.
        processed_dir: Path to processed data directory.
        analysis_dir: Path to analysis data directory.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    raw_dir = raw_dir or get_raw_dir()
    processed_dir = processed_dir or get_processed_dir()
    analysis_dir = analysis_dir or get_analysis_dir()
    algorithm = get_checksum_algorithm()

    artifacts = {}
    directories = [d for d in [raw_dir, processed_dir, analysis_dir] if d and d.exists()]

    for directory in directories:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(get_data_root()))
                try:
                    checksum = compute_file_checksum(file_path, algorithm)
                    artifacts[rel_path] = checksum
                    logger.info(f"Computed checksum for {rel_path}: {checksum[:16]}...")
                except Exception as e:
                    logger.warning(f"Skipping {rel_path} due to error: {e}")

    return artifacts

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the existing manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Manifest dictionary.
    """
    manifest_path = manifest_path or MANIFEST_PATH
    if not manifest_path.exists():
        return {"artifacts": {}, "metadata": {}}
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in manifest: {manifest_path}")
        return {"artifacts": {}, "metadata": {}}

def save_manifest(manifest: Dict[str, Any], manifest_path: Optional[Path] = None) -> None:
    """
    Save the manifest to disk.

    Args:
        manifest: Manifest dictionary to save.
        manifest_path: Path to save the manifest.
    """
    manifest_path = manifest_path or MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved manifest to {manifest_path}")

def record_artifact_checksums(
    checksums: Dict[str, str],
    manifest_path: Optional[Path] = None
) -> None:
    """
    Record artifact checksums in the manifest.

    Args:
        checksums: Dictionary of file paths to checksums.
        manifest_path: Path to the manifest file.
    """
    manifest = load_manifest(manifest_path)
    manifest["artifacts"].update(checksums)
    manifest["metadata"]["last_updated"] = datetime.now().isoformat()
    save_manifest(manifest, manifest_path)
    logger.info(f"Recorded checksums for {len(checksums)} artifacts.")

def verify_artifact_checksums(manifest_path: Optional[Path] = None) -> bool:
    """
    Verify all artifacts against the stored checksums.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        True if all checksums match, False otherwise.
    """
    manifest = load_manifest(manifest_path)
    stored_checksums = manifest.get("artifacts", {})
    if not stored_checksums:
        logger.warning("No checksums found in manifest.")
        return False

    all_valid = True
    for rel_path, stored_hash in stored_checksums.items():
        full_path = get_data_root() / rel_path
        if not full_path.exists():
            logger.error(f"Artifact missing: {rel_path}")
            all_valid = False
            continue
        try:
            current_hash = compute_file_checksum(full_path)
            if current_hash != stored_hash:
                logger.error(f"Checksum mismatch for {rel_path}")
                all_valid = False
            else:
                logger.info(f"Verified: {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            all_valid = False

    return all_valid

def get_artifact_hashes(manifest_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Get the dictionary of artifact hashes from the manifest.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary mapping file paths to checksums.
    """
    manifest = load_manifest(manifest_path)
    return manifest.get("artifacts", {})

def add_custom_artifact(
    file_path: Path,
    relative_name: str,
    manifest_path: Optional[Path] = None
) -> None:
    """
    Add a specific artifact to the manifest.

    Args:
        file_path: Absolute path to the file.
        relative_name: Name to use in the manifest.
        manifest_path: Path to the manifest file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Custom artifact not found: {file_path}")
    checksum = compute_file_checksum(file_path)
    checksums = {relative_name: checksum}
    record_artifact_checksums(checksums, manifest_path)
    logger.info(f"Added custom artifact: {relative_name}")

def main() -> None:
    """Main entry point for checksum manifest generation."""
    setup_logging()
    logger.info("Starting checksum manifest generation...")

    # Compute checksums for all data directories
    checksums = compute_all_artifact_checksums()

    if not checksums:
        logger.warning("No artifacts found to checksum.")
        return

    # Record in manifest
    record_artifact_checksums(checksums)

    # Verify
    if verify_artifact_checksums():
        logger.info("All artifact checksums verified successfully.")
    else:
        logger.error("Checksum verification failed.")

if __name__ == "__main__":
    main()