"""
Checksum Manifest Module for llmXive Project PROJ-261

This module provides infrastructure for tracking artifact checksums
to ensure reproducibility and data integrity.

SC-006: Checksum tracking for all artifacts
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup module-level logger
logger = logging.getLogger(__name__)

# Default manifest path
DEFAULT_MANIFEST_PATH = Path("data/analysis/artifact_checksums.json")

# Supported hash algorithms
SUPPORTED_ALGORITHMS = ['sha256', 'md5', 'sha1']
DEFAULT_ALGORITHM = 'sha256'

def setup_logging():
    """Configure logging for checksum operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logger

def compute_file_checksum(file_path: Path, algorithm: str = DEFAULT_ALGORITHM) -> str:
    """
    Compute checksum for a single file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (sha256, md5, sha1)
    
    Returns:
        Hex digest of the file checksum
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm is not supported
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def compute_all_artifact_checksums(
    artifact_paths: List[Path],
    algorithm: str = DEFAULT_ALGORITHM
) -> Dict[str, str]:
    """
    Compute checksums for multiple artifact files.
    
    Args:
        artifact_paths: List of paths to artifact files
        algorithm: Hash algorithm to use
    
    Returns:
        Dict mapping relative paths to checksums
    """
    checksums = {}
    
    for path in artifact_paths:
        try:
            checksum = compute_file_checksum(path, algorithm)
            checksums[str(path)] = checksum
            logger.info(f"Computed checksum for {path}: {checksum[:16]}...")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Failed to compute checksum for {path}: {e}")
    
    return checksums

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load checksum manifest from file.
    
    Args:
        manifest_path: Path to the manifest JSON file
    
    Returns:
        Manifest dictionary with checksums and metadata
    
    Note:
        manifest_path must be a Path object, not a dict or string.
    """
    if not isinstance(manifest_path, Path):
        raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
    
    if not manifest_path.exists():
        logger.info(f"Manifest not found, creating new: {manifest_path}")
        return {
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'artifact_hashes': {},
            'metadata': {
                'algorithm': DEFAULT_ALGORITHM,
                'project': 'PROJ-261-evaluating-the-impact-of-code-duplication'
            }
        }
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logger.info(f"Loaded existing manifest: {manifest_path}")
        return manifest
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest JSON: {e}")
        raise

def save_manifest(manifest: Dict[str, Any], manifest_path: Path) -> None:
    """
    Save checksum manifest to file.
    
    Args:
        manifest: Manifest dictionary to save
        manifest_path: Path to save the manifest
    """
    if not isinstance(manifest_path, Path):
        raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
    
    manifest['updated_at'] = datetime.utcnow().isoformat()
    
    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Saved manifest to {manifest_path}")

def record_artifact_checksums(
    artifact_paths: List[Path],
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    algorithm: str = DEFAULT_ALGORITHM
) -> Dict[str, Any]:
    """
    Compute checksums for artifacts and record in manifest.
    
    Args:
        artifact_paths: List of artifact file paths
        manifest_path: Path to the manifest file
        algorithm: Hash algorithm to use
    
    Returns:
        Updated manifest dictionary
    """
    if not isinstance(manifest_path, Path):
        raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
    
    # Load existing manifest
    manifest = load_manifest(manifest_path)
    
    # Compute new checksums
    new_checksums = compute_all_artifact_checksums(artifact_paths, algorithm)
    
    # Update manifest
    if 'artifact_hashes' not in manifest:
        manifest['artifact_hashes'] = {}
    
    manifest['artifact_hashes'].update(new_checksums)
    
    # Save updated manifest
    save_manifest(manifest, manifest_path)
    
    logger.info(f"Recorded checksums for {len(new_checksums)} artifacts")
    return manifest

def verify_artifact_checksums(
    artifact_paths: List[Path],
    manifest_path: Path = DEFAULT_MANIFEST_PATH
) -> Dict[str, bool]:
    """
    Verify artifact checksums against manifest.
    
    Args:
        artifact_paths: List of artifact file paths to verify
        manifest_path: Path to the manifest file
    
    Returns:
        Dict mapping paths to verification status (True = valid)
    """
    if not isinstance(manifest_path, Path):
        raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
    
    manifest = load_manifest(manifest_path)
    stored_checksums = manifest.get('artifact_hashes', {})
    
    results = {}
    
    for path in artifact_paths:
        path_str = str(path)
        
        if path_str not in stored_checksums:
            logger.warning(f"No stored checksum for {path}")
            results[path_str] = False
            continue
        
        try:
            current_checksum = compute_file_checksum(path)
            stored_checksum = stored_checksums[path_str]
            is_valid = current_checksum == stored_checksum
            results[path_str] = is_valid
            
            if is_valid:
                logger.info(f"Checksum verified for {path}")
            else:
                logger.error(f"Checksum mismatch for {path}")
                logger.error(f"  Current: {current_checksum}")
                logger.error(f"  Stored:  {stored_checksum}")
        except FileNotFoundError:
            logger.error(f"File not found for verification: {path}")
            results[path_str] = False
    
    return results

def get_artifact_hashes(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> Dict[str, str]:
    """
    Get all artifact hashes from manifest.
    
    Args:
        manifest_path: Path to the manifest file
    
    Returns:
        Dict mapping paths to checksums
    """
    if not isinstance(manifest_path, Path):
        raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
    
    manifest = load_manifest(manifest_path)
    return manifest.get('artifact_hashes', {})

def add_custom_artifact(
    artifact_name: str,
    checksum: str,
    manifest_path: Path = DEFAULT_MANIFEST_PATH
) -> Dict[str, Any]:
    """
    Add a custom artifact entry to the manifest.
    
    Args:
        artifact_name: Name/identifier for the artifact
        checksum: Pre-computed checksum value
        manifest_path: Path to the manifest file
    
    Returns:
        Updated manifest dictionary
    """
    if not isinstance(manifest_path, Path):
        raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
    
    manifest = load_manifest(manifest_path)
    
    if 'artifact_hashes' not in manifest:
        manifest['artifact_hashes'] = {}
    
    manifest['artifact_hashes'][artifact_name] = checksum
    save_manifest(manifest, manifest_path)
    
    logger.info(f"Added custom artifact: {artifact_name}")
    return manifest

def main():
    """Command-line interface for checksum operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Checksum Manifest Management')
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST_PATH,
                      help='Path to manifest file')
    parser.add_argument('--add', nargs='+', type=Path,
                      help='Add artifacts to manifest')
    parser.add_argument('--verify', nargs='+', type=Path,
                      help='Verify artifacts against manifest')
    parser.add_argument('--show', action='store_true',
                      help='Display current manifest')
    
    args = parser.parse_args()
    
    if args.add:
        manifest = record_artifact_checksums(args.add, args.manifest)
        print(f"Recorded checksums for {len(args.add)} artifacts")
    
    elif args.verify:
        results = verify_artifact_checksums(args.verify, args.manifest)
        valid_count = sum(1 for v in results.values() if v)
        print(f"Verified {valid_count}/{len(results)} artifacts")
    
    elif args.show:
        manifest = load_manifest(args.manifest)
        print(json.dumps(manifest, indent=2))
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
