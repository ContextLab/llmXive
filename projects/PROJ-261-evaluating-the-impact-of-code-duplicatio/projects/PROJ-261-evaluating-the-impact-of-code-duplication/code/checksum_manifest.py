"""
Checksum manifest module for artifact tracking and reproducibility.

Implements SC-006 by computing and storing checksums for all output files,
intermediate files, and logs to ensure data integrity and versioning.
"""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import PROJECT_ROOT, get_checksum_algorithm

# Configure logging
logger = logging.getLogger(__name__)

MANIFEST_PATH = PROJECT_ROOT / 'data' / 'analysis' / 'checksum_manifest.json'

def setup_logging() -> None:
    """Configure logging for the manifest module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def compute_file_checksum(file_path: Path, algorithm: str = None) -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: from config).

    Returns:
        Hex digest of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm is None:
        algorithm = get_checksum_algorithm()

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()

def compute_all_artifact_checksums(
    artifact_paths: List[Path],
    algorithm: str = None
) -> Dict[str, str]:
    """
    Compute checksums for multiple artifacts.

    Args:
        artifact_paths: List of file paths to checksum.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping file paths (as strings) to checksums.
    """
    checksums = {}
    for path in artifact_paths:
        try:
            checksums[str(path)] = compute_file_checksum(path, algorithm)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not compute checksum for {path}: {e}")
    return checksums

def load_manifest() -> Optional[Dict[str, Any]]:
    """
    Load the existing checksum manifest.

    Returns:
        Manifest dictionary or None if file does not exist.
    """
    if not MANIFEST_PATH.exists():
        return None

    try:
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load manifest: {e}")
        return None

def save_manifest(manifest: Dict[str, Any]) -> None:
    """
    Save the checksum manifest to disk.

    Args:
        manifest: Manifest dictionary to save.
    """
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)
    logger.info(f"Manifest saved to {MANIFEST_PATH}")

def record_artifact_checksums(
    artifact_hashes: Dict[str, str],
    component: str = None
) -> None:
    """
    Record artifact checksums in the manifest.

    Args:
        artifact_hashes: Dictionary of file paths to checksums.
        component: Optional component name for grouping.
    """
    manifest = load_manifest() or {
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'artifact_hashes': {},
        'components': {}
    }

    manifest['updated_at'] = datetime.now().isoformat()

    if component:
        if 'components' not in manifest:
            manifest['components'] = {}
        manifest['components'][component] = {
            'updated_at': datetime.now().isoformat(),
            'artifacts': list(artifact_hashes.keys())
        }

    manifest['artifact_hashes'].update(artifact_hashes)
    save_manifest(manifest)

def verify_artifact_checksums(
    artifact_paths: List[Path],
    expected_hashes: Dict[str, str] = None
) -> bool:
    """
    Verify that artifact checksums match expected values.

    Args:
        artifact_paths: List of file paths to verify.
        expected_hashes: Optional dictionary of expected checksums.

    Returns:
        True if all checksums match, False otherwise.
    """
    if expected_hashes is None:
        manifest = load_manifest()
        if manifest is None:
            logger.warning("No manifest found for verification")
            return False
        expected_hashes = manifest.get('artifact_hashes', {})

    all_valid = True
    for path in artifact_paths:
        path_str = str(path)
        if path_str not in expected_hashes:
            logger.warning(f"No expected checksum for {path_str}")
            continue

        try:
            actual_hash = compute_file_checksum(path)
            if actual_hash != expected_hashes[path_str]:
                logger.error(f"Checksum mismatch for {path_str}")
                all_valid = False
            else:
                logger.info(f"Checksum verified for {path_str}")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to verify {path_str}: {e}")
            all_valid = False

    return all_valid

def get_artifact_hashes() -> Dict[str, str]:
    """
    Get all artifact hashes from the manifest.

    Returns:
        Dictionary of file paths to checksums.
    """
    manifest = load_manifest()
    if manifest is None:
        return {}
    return manifest.get('artifact_hashes', {})

def add_custom_artifact(
    file_path: Path,
    custom_name: str = None
) -> str:
    """
    Add a custom artifact to the manifest.

    Args:
        file_path: Path to the artifact file.
        custom_name: Optional custom name for the artifact.

    Returns:
        The computed checksum.
    """
    checksum = compute_file_checksum(file_path)
    name = custom_name or str(file_path)
    record_artifact_checksums({name: checksum})
    return checksum

def main() -> None:
    """Main entry point for checksum manifest operations."""
    setup_logging()
    logger.info("Checksum manifest module loaded")
    logger.info(f"Manifest path: {MANIFEST_PATH}")

    # Example: list all tracked artifacts
    hashes = get_artifact_hashes()
    if hashes:
        logger.info(f"Tracked artifacts: {len(hashes)}")
        for name, checksum in hashes.items():
            logger.info(f"  {name}: {checksum[:16]}...")
    else:
        logger.info("No artifacts tracked yet")

if __name__ == '__main__':
    main()