"""
Checksum Manager for verifying downloaded artifacts in data/raw/.

This module provides functionality to:
1. Compute SHA256 checksums for files in the data/raw directory.
2. Save checksums to a manifest file (data/raw/checksums.json).
3. Verify existing files against the manifest.
4. Update checksums when files are added or modified.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_project_root() -> Path:
    """
    Get the project root directory (assumed to be 4 levels up from this file).
    
    Returns:
        Path: Project root directory
    """
    return Path(__file__).resolve().parent.parent.parent.parent


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        str: Hexadecimal checksum string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def load_checksum_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the checksum manifest file.
    
    Args:
        manifest_path: Path to the manifest JSON file
        
    Returns:
        Dict containing the manifest data
        
    Raises:
        FileNotFoundError: If manifest does not exist
        json.JSONDecodeError: If manifest is not valid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)


def save_checksum_manifest(manifest_path: Path, manifest_data: Dict[str, Any]) -> None:
    """
    Save the checksum manifest to a JSON file.
    
    Args:
        manifest_path: Path to save the manifest
        manifest_data: Dictionary containing checksum data
    """
    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Saved checksum manifest to {manifest_path}")


def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> Tuple[bool, str]:
    """
    Verify a single file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected checksum string
        algorithm: Hash algorithm to use
        
    Returns:
        Tuple of (is_valid, computed_checksum)
    """
    try:
        computed = compute_file_checksum(file_path, algorithm)
        is_valid = computed == expected_checksum
        if not is_valid:
            logger.warning(f"Checksum mismatch for {file_path.name}")
            logger.warning(f"  Expected: {expected_checksum}")
            logger.warning(f"  Computed: {computed}")
        else:
            logger.info(f"Checksum verified for {file_path.name}")
        return is_valid, computed
    except Exception as e:
        logger.error(f"Error verifying {file_path}: {e}")
        return False, str(e)


def verify_all_files(raw_dir: Path, manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Verify all files in data/raw/ against the checksum manifest.
    
    Args:
        raw_dir: Path to the data/raw directory
        manifest_path: Optional path to manifest (defaults to raw_dir/checksums.json)
        
    Returns:
        Dict with verification results:
            - all_valid: bool
            - verified_files: list of (filename, status) tuples
            - missing_files: list of filenames missing from disk
            - new_files: list of filenames not in manifest
    """
    if manifest_path is None:
        manifest_path = raw_dir / 'checksums.json'
    
    result = {
        'all_valid': True,
        'verified_files': [],
        'missing_files': [],
        'new_files': []
    }
    
    # Load manifest
    if not manifest_path.exists():
        logger.warning(f"No checksum manifest found at {manifest_path}")
        result['all_valid'] = False
        # Scan for files anyway
        for file_path in raw_dir.iterdir():
            if file_path.is_file() and file_path.name != 'checksums.json':
                result['new_files'].append(file_path.name)
        return result
    
    manifest = load_checksum_manifest(manifest_path)
    manifest_files = manifest.get('files', {})
    
    # Check files in manifest
    for filename, info in manifest_files.items():
        file_path = raw_dir / filename
        
        if not file_path.exists():
            logger.error(f"File missing: {filename}")
            result['missing_files'].append(filename)
            result['all_valid'] = False
            continue
        
        is_valid, _ = verify_checksum(file_path, info['checksum'])
        status = 'valid' if is_valid else 'invalid'
        result['verified_files'].append((filename, status))
        
        if not is_valid:
            result['all_valid'] = False
    
    # Check for new files not in manifest
    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.name != 'checksums.json':
            if file_path.name not in manifest_files:
                result['new_files'].append(file_path.name)
    
    return result


def update_checksum_for_file(file_path: Path, manifest_path: Path) -> None:
    """
    Update the checksum for a specific file in the manifest.
    
    Args:
        file_path: Path to the file
        manifest_path: Path to the manifest file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Load existing manifest or create new
    if manifest_path.exists():
        manifest = load_checksum_manifest(manifest_path)
    else:
        manifest = {'files': {}, 'metadata': {}}
    
    if 'files' not in manifest:
        manifest['files'] = {}
    
    # Compute and update checksum
    checksum = compute_file_checksum(file_path)
    file_info = {
        'checksum': checksum,
        'algorithm': 'sha256',
        'size': file_path.stat().st_size,
        'updated_at': str(Path(__file__).parent)  # Could be improved with datetime
    }
    
    manifest['files'][file_path.name] = file_info
    save_checksum_manifest(manifest_path, manifest)
    logger.info(f"Updated checksum for {file_path.name}")


def main():
    """
    CLI entry point for checksum management.
    
    Usage:
        python -m src.data.checksum_manager [command] [options]
        
    Commands:
        verify    Verify all files in data/raw/
        update    Update checksums for all files in data/raw/
        add       Add a specific file to the manifest
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Checksum management for data/raw/')
    parser.add_argument('command', choices=['verify', 'update', 'add'],
                      help='Command to execute')
    parser.add_argument('--file', type=str, help='Specific file for add command')
    parser.add_argument('--raw-dir', type=str, default=None,
                      help='Path to data/raw directory (default: auto-detect)')
    
    args = parser.parse_args()
    
    # Determine raw directory
    if args.raw_dir:
        raw_dir = Path(args.raw_dir)
    else:
        raw_dir = get_project_root() / 'data' / 'raw'
    
    if not raw_dir.exists():
        logger.error(f"Raw directory not found: {raw_dir}")
        sys.exit(1)
    
    manifest_path = raw_dir / 'checksums.json'
    
    if args.command == 'verify':
        logger.info(f"Verifying files in {raw_dir}")
        result = verify_all_files(raw_dir, manifest_path)
        
        if result['all_valid']:
            logger.info("All files verified successfully")
        else:
            logger.warning("Verification completed with issues:")
            if result['missing_files']:
                logger.warning(f"  Missing: {result['missing_files']}")
            if result['new_files']:
                logger.warning(f"  New (not in manifest): {result['new_files']}")
            if any(status == 'invalid' for _, status in result['verified_files']):
                logger.warning("  Some files have invalid checksums")
        
        sys.exit(0 if result['all_valid'] else 1)
    
    elif args.command == 'update':
        logger.info(f"Updating checksums for all files in {raw_dir}")
        for file_path in raw_dir.iterdir():
            if file_path.is_file() and file_path.name != 'checksums.json':
                update_checksum_for_file(file_path, manifest_path)
        logger.info("Checksum update complete")
    
    elif args.command == 'add':
        if not args.file:
            logger.error("--file is required for add command")
            sys.exit(1)
        
        file_path = raw_dir / args.file
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
        
        update_checksum_for_file(file_path, manifest_path)
        logger.info(f"Added {args.file} to manifest")


if __name__ == '__main__':
    main()
