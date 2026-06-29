"""
Checksum manifest management for artifact verification.

This module provides infrastructure for tracking and verifying artifact
checksums throughout the research pipeline.

Features:
- Compute checksums for files
- Save/load manifest JSON
- Record artifact checksums
- Verify artifact integrity
"""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logger = logging.getLogger(__name__)


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the module."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logger


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute checksum for a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the file checksum
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def compute_all_artifact_checksums(
    artifact_paths: List[Path],
    algorithm: str = 'sha256'
) -> Dict[str, str]:
    """
    Compute checksums for multiple artifacts.

    Args:
        artifact_paths: List of file paths to checksum
        algorithm: Hash algorithm to use

    Returns:
        Dictionary mapping file paths to checksums
    """
    checksums = {}

    for path in artifact_paths:
        if path.exists():
            try:
                checksum = compute_file_checksum(path, algorithm)
                checksums[str(path)] = checksum
            except Exception as e:
                logger.warning(f"Failed to compute checksum for {path}: {e}")
        else:
            logger.warning(f"File not found for checksum: {path}")

    return checksums


def load_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load manifest from JSON file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        Manifest dictionary or None if not found/invalid
    """
    # Ensure manifest_path is a Path object, not a dict
    if isinstance(manifest_path, dict):
        logger.error("manifest_path is a dict, not a Path object")
        return None

    if not manifest_path.exists():
        logger.info(f"Manifest not found: {manifest_path}")
        return None

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logger.info(f"Loaded manifest from: {manifest_path}")
        return manifest
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return None


def save_manifest(manifest: Dict[str, Any], manifest_path: Path) -> bool:
    """
    Save manifest to JSON file.

    Args:
        manifest: Manifest dictionary to save
        manifest_path: Path to save manifest to

    Returns:
        True if successful, False otherwise
    """
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)

        logger.info(f"Saved manifest to: {manifest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")
        return False


def record_artifact_checksums(
    artifact_dir: Path,
    manifest_path: Optional[Path] = None,
    algorithm: str = 'sha256'
) -> Dict[str, str]:
    """
    Record checksums for all artifacts in a directory.

    Args:
        artifact_dir: Directory containing artifacts
        manifest_path: Path to save manifest (default: artifact_dir/manifest.json)
        algorithm: Hash algorithm to use

    Returns:
        Dictionary of artifact checksums
    """
    if manifest_path is None:
        manifest_path = artifact_dir / 'manifest.json'

    # Ensure manifest_path is a Path object
    if not isinstance(manifest_path, Path):
        manifest_path = Path(manifest_path)

    # Find all artifact files
    artifact_files = []
    for ext in ['*.csv', '*.json', '*.log', '*.png', '*.pdf']:
        artifact_files.extend(artifact_dir.glob(ext))

    # Compute checksums
    checksums = compute_all_artifact_checksums(artifact_files, algorithm)

    # Load existing manifest or create new one
    manifest = load_manifest(manifest_path) or {
        'created_at': datetime.now().isoformat(),
        'artifact_hashes': {},
        'algorithm': algorithm
    }

    # Update checksums
    manifest['artifact_hashes'].update(checksums)
    manifest['updated_at'] = datetime.now().isoformat()

    # Save manifest
    save_manifest(manifest, manifest_path)

    logger.info(f"Recorded {len(checksums)} artifact checksums")
    return checksums


def verify_artifact_checksums(
    artifact_dir: Path,
    manifest_path: Optional[Path] = None,
    algorithm: str = 'sha256'
) -> Dict[str, bool]:
    """
    Verify artifact checksums against manifest.

    Args:
        artifact_dir: Directory containing artifacts
        manifest_path: Path to manifest file
        algorithm: Hash algorithm to use

    Returns:
        Dictionary mapping file paths to verification status
    """
    if manifest_path is None:
        manifest_path = artifact_dir / 'manifest.json'

    # Ensure manifest_path is a Path object
    if not isinstance(manifest_path, Path):
        manifest_path = Path(manifest_path)

    manifest = load_manifest(manifest_path)
    if manifest is None:
        logger.error("No manifest found for verification")
        return {}

    stored_checksums = manifest.get('artifact_hashes', {})
    verification_results = {}

    for file_path_str, stored_checksum in stored_checksums.items():
        file_path = Path(file_path_str)

        if not file_path.exists():
            verification_results[file_path_str] = False
            logger.warning(f"File not found for verification: {file_path}")
            continue

        try:
            computed_checksum = compute_file_checksum(file_path, algorithm)
            verification_results[file_path_str] = (computed_checksum == stored_checksum)

            if not verification_results[file_path_str]:
                logger.warning(f"Checksum mismatch for {file_path}")
            else:
                logger.info(f"Checksum verified for {file_path}")
        except Exception as e:
            logger.error(f"Failed to verify {file_path}: {e}")
            verification_results[file_path_str] = False

    return verification_results


def get_artifact_hashes(
    artifact_dir: Path,
    manifest_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Get artifact checksums from manifest.

    Args:
        artifact_dir: Directory containing artifacts
        manifest_path: Path to manifest file

    Returns:
        Dictionary of artifact checksums
    """
    if manifest_path is None:
        manifest_path = artifact_dir / 'manifest.json'

    # Ensure manifest_path is a Path object
    if not isinstance(manifest_path, Path):
        manifest_path = Path(manifest_path)

    manifest = load_manifest(manifest_path)
    if manifest is None:
        return {}

    return manifest.get('artifact_hashes', {})


def add_custom_artifact(
    artifact_path: Path,
    manifest_path: Path,
    algorithm: str = 'sha256'
) -> bool:
    """
    Add a custom artifact to the manifest.

    Args:
        artifact_path: Path to the artifact file
        manifest_path: Path to manifest file
        algorithm: Hash algorithm to use

    Returns:
        True if successful, False otherwise
    """
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        return False

    # Ensure manifest_path is a Path object
    if not isinstance(manifest_path, Path):
        manifest_path = Path(manifest_path)

    checksum = compute_file_checksum(artifact_path, algorithm)

    manifest = load_manifest(manifest_path) or {
        'created_at': datetime.now().isoformat(),
        'artifact_hashes': {},
        'algorithm': algorithm
    }

    manifest['artifact_hashes'][str(artifact_path)] = checksum
    manifest['updated_at'] = datetime.now().isoformat()

    return save_manifest(manifest, manifest_path)


def main():
    """Main entry point for checksum manifest CLI."""
    import argparse

    parser = argparse.ArgumentParser(description='Checksum manifest management')
    parser.add_argument('command', choices=['record', 'verify', 'get'],
                      help='Command to execute')
    parser.add_argument('--dir', type=Path, default=Path('data'),
                      help='Artifact directory')
    parser.add_argument('--manifest', type=Path, default=None,
                      help='Manifest file path')
    parser.add_argument('--algorithm', type=str, default='sha256',
                      help='Hash algorithm')

    args = parser.parse_args()

    if args.command == 'record':
        record_artifact_checksums(args.dir, args.manifest, args.algorithm)
    elif args.command == 'verify':
        results = verify_artifact_checksums(args.dir, args.manifest, args.algorithm)
        print(f"Verification results: {results}")
    elif args.command == 'get':
        hashes = get_artifact_hashes(args.dir, args.manifest)
        print(f"Artifact hashes: {hashes}")


if __name__ == '__main__':
    main()