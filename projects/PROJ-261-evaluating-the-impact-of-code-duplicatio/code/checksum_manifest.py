"""
Checksum Manifest Management for Artifact Tracking

This module provides functionality to compute, store, and verify
checksums for all project artifacts to ensure data integrity and
reproducibility per Constitution Principle V (Versioning Discipline).
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure module logging
logger = logging.getLogger(__name__)

# Default manifest location
DEFAULT_MANIFEST_PATH = Path("data/analysis/checksum_manifest.json")

# Supported hash algorithms
SUPPORTED_ALGORITHMS = ["sha256", "md5", "sha1"]


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for checksum operations."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Compute checksum for a single file.

    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (sha256, md5, sha1)

    Returns:
        Hex digest string or None if file doesn't exist
    """
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return None

    if algorithm not in SUPPORTED_ALGORITHMS:
        logger.error(f"Unsupported algorithm: {algorithm}")
        return None

    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return None


def compute_all_artifact_checksums(
    artifact_paths: List[Path],
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Compute checksums for multiple artifacts.

    Args:
        artifact_paths: List of file paths to checksum
        algorithm: Hash algorithm to use

    Returns:
        Dictionary mapping file paths (as strings) to checksums
    """
    checksums = {}
    for path in artifact_paths:
        checksum = compute_file_checksum(path, algorithm)
        if checksum:
            checksums[str(path)] = checksum
        else:
            logger.warning(f"Skipping missing file: {path}")
    return checksums


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load checksum manifest from file.

    Args:
        manifest_path: Path to manifest JSON file

    Returns:
        Manifest dictionary or empty dict if file doesn't exist
    """
    if not manifest_path.exists():
        logger.info(f"Manifest not found, creating new: {manifest_path}")
        return {
            "created_at": datetime.now().isoformat(),
            "artifact_hashes": {},
            "metadata": {
                "algorithm": "sha256",
                "version": "1.0"
            }
        }

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logger.info(f"Loaded manifest from {manifest_path}")
        return manifest
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return {
            "created_at": datetime.now().isoformat(),
            "artifact_hashes": {},
            "metadata": {
                "algorithm": "sha256",
                "version": "1.0"
            }
        }


def save_manifest(manifest_path: Path, manifest: Dict[str, Any]) -> None:
    """
    Save checksum manifest to file.

    Args:
        manifest_path: Path to save manifest to (MUST be Path object)
        manifest: Manifest dictionary to save
    """
    # Ensure manifest_path is a Path object, not a dict
    if not isinstance(manifest_path, Path):
        logger.error(f"manifest_path must be a Path object, got {type(manifest_path)}")
        raise TypeError(f"manifest_path must be Path, got {type(manifest_path)}")

    # Create parent directories if needed
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Update metadata
    manifest["updated_at"] = datetime.now().isoformat()

    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        logger.info(f"Saved manifest to {manifest_path}")
    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")
        raise


def record_artifact_checksums(
    manifest_path: Path,
    artifact_checksums: Dict[str, str],
    category: str = "general"
) -> Dict[str, Any]:
    """
    Record artifact checksums in manifest.

    Args:
        manifest_path: Path to manifest file
        artifact_checksums: Dictionary of file paths to checksums
        category: Category label for these artifacts

    Returns:
        Updated manifest dictionary
    """
    manifest = load_manifest(manifest_path)

    # Initialize category if needed
    if category not in manifest.get("artifact_hashes", {}):
        if "artifact_hashes" not in manifest:
            manifest["artifact_hashes"] = {}
        manifest["artifact_hashes"][category] = {}

    # Add checksums
    for path, checksum in artifact_checksums.items():
        manifest["artifact_hashes"][category][path] = {
            "checksum": checksum,
            "recorded_at": datetime.now().isoformat()
        }

    save_manifest(manifest_path, manifest)
    return manifest


def verify_artifact_checksums(
    manifest_path: Path,
    category: str = "general"
) -> Dict[str, bool]:
    """
    Verify checksums for artifacts in a category.

    Args:
        manifest_path: Path to manifest file
        category: Category to verify

    Returns:
        Dictionary mapping paths to verification status (True/False)
    """
    manifest = load_manifest(manifest_path)
    verification_results = {}

    if category not in manifest.get("artifact_hashes", {}):
        logger.warning(f"No artifacts found in category: {category}")
        return verification_results

    for path_str, artifact_info in manifest["artifact_hashes"][category].items():
        path = Path(path_str)
        expected_checksum = artifact_info.get("checksum")

        if expected_checksum:
            actual_checksum = compute_file_checksum(path)
            if actual_checksum:
                verification_results[path_str] = actual_checksum == expected_checksum
            else:
                verification_results[path_str] = False
        else:
            verification_results[path_str] = False

    return verification_results


def get_artifact_hashes(
    manifest_path: Path,
    category: Optional[str] = None
) -> Dict[str, str]:
    """
    Get artifact checksums from manifest.

    Args:
        manifest_path: Path to manifest file
        category: Optional category filter

    Returns:
        Dictionary mapping file paths to checksums
    """
    manifest = load_manifest(manifest_path)

    if category:
        if category in manifest.get("artifact_hashes", {}):
            return {
                path: info.get("checksum", "")
                for path, info in manifest["artifact_hashes"][category].items()
            }
        return {}

    # Return all checksums flattened
    all_hashes = {}
    for cat, artifacts in manifest.get("artifact_hashes", {}).items():
        for path, info in artifacts.items():
            all_hashes[path] = info.get("checksum", "")

    return all_hashes


def add_custom_artifact(
    manifest_path: Path,
    artifact_path: Path,
    category: str,
    description: str = ""
) -> bool:
    """
    Add a custom artifact to the manifest with computed checksum.

    Args:
        manifest_path: Path to manifest file
        artifact_path: Path to the artifact file
        category: Category to add artifact to
        description: Optional description of the artifact

    Returns:
        True if successful, False otherwise
    """
    checksum = compute_file_checksum(artifact_path)
    if not checksum:
        logger.error(f"Could not compute checksum for: {artifact_path}")
        return False

    manifest = load_manifest(manifest_path)

    if category not in manifest.get("artifact_hashes", {}):
        if "artifact_hashes" not in manifest:
            manifest["artifact_hashes"] = {}
        manifest["artifact_hashes"][category] = {}

    manifest["artifact_hashes"][category][str(artifact_path)] = {
        "checksum": checksum,
        "recorded_at": datetime.now().isoformat(),
        "description": description
    }

    save_manifest(manifest_path, manifest)
    return True


def main():
    """Main entry point for checksum manifest operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Checksum Manifest Management")
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to checksum manifest file"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="sha256",
        choices=SUPPORTED_ALGORITHMS,
        help="Hash algorithm to use"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify artifact checksums"
    )
    parser.add_argument(
        "--category",
        type=str,
        default="general",
        help="Category for artifacts"
    )

    args = parser.parse_args()

    setup_logging()

    if args.verify:
        results = verify_artifact_checksums(args.manifest_path, args.category)
        for path, valid in results.items():
            status = "✓" if valid else "✗"
            print(f"{status} {path}")
        return 0 if all(results.values()) else 1
    else:
        print(f"Checksum manifest at: {args.manifest_path}")
        manifest = load_manifest(args.manifest_path)
        print(json.dumps(manifest, indent=2))
        return 0


if __name__ == "__main__":
    exit(main())
