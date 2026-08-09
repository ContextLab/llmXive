"""
Checksum utility for dataset integrity verification.

This module provides functions to calculate SHA-256 checksums for files and directories,
save/load checksum manifests, and verify data integrity against stored checksums.

Usage:
    from utils.checksum import calculate_file_checksum, save_checksum_manifest, verify_file_checksum
    
    # Calculate checksum for a single file
    checksum = calculate_file_checksum('data/raw/chunk_0.parquet')
    
    # Save manifest for multiple files
    files = ['data/raw/chunk_0.parquet', 'data/raw/chunk_1.parquet']
    save_checksum_manifest(files, 'data/raw/checksums.json')
    
    # Verify a file against manifest
    is_valid = verify_file_checksum('data/raw/chunk_0.parquet', 'data/raw/checksums.json')
"""

import hashlib
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .config import get_project_root, get_data_dir
from .logging import get_logger

# Constants
CHECKSUM_ALGORITHM = 'sha256'
CHUNK_SIZE = 8192  # Read files in 8KB chunks for memory efficiency

# Logger setup
logger = get_logger(__name__)

def calculate_file_checksum(file_path: str, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Calculate the SHA-256 checksum of a single file.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string representation of the checksum
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE):
                hash_obj.update(chunk)
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise
    
    return hash_obj.hexdigest()

def calculate_directory_checksum(
    dir_path: str, 
    pattern: Optional[str] = None,
    recursive: bool = True,
    algorithm: str = CHECKSUM_ALGORITHM
) -> Dict[str, str]:
    """
    Calculate checksums for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        pattern: Optional glob pattern to filter files (e.g., '*.parquet')
        recursive: Whether to search subdirectories
        algorithm: Hash algorithm to use
        
    Returns:
        Dictionary mapping relative file paths to their checksums
        
    Raises:
        NotADirectoryError: If the path is not a directory
    """
    dir_path = Path(dir_path)
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    checksums = {}
    
    if recursive:
        files = dir_path.rglob('*')
    else:
        files = dir_path.glob('*')
    
    for file_path in files:
        if file_path.is_file():
            # Apply pattern filter if specified
            if pattern and not file_path.match(pattern):
                continue
            
            # Calculate relative path from the directory
            rel_path = str(file_path.relative_to(dir_path))
            
            try:
                checksum = calculate_file_checksum(str(file_path), algorithm)
                checksums[rel_path] = checksum
                logger.debug(f"Calculated checksum for {rel_path}: {checksum[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to calculate checksum for {rel_path}: {e}")
    
    return checksums

def save_checksum_manifest(
    checksums: Dict[str, str],
    manifest_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary mapping file paths to checksums
        manifest_path: Path where the manifest should be saved
        metadata: Optional metadata to include (e.g., creation timestamp, algorithm)
    """
    manifest_path = Path(manifest_path)
    
    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_data = {
        'algorithm': CHECKSUM_ALGORITHM,
        'created_at': None,  # Can be set by caller if needed
        'checksums': checksums,
        'metadata': metadata or {}
    }
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"Saved checksum manifest to {manifest_path}")
    except IOError as e:
        logger.error(f"Failed to write manifest {manifest_path}: {e}")
        raise

def load_checksum_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        Dictionary containing manifest data
        
    Raises:
        FileNotFoundError: If the manifest does not exist
        json.JSONDecodeError: If the manifest is not valid JSON
    """
    manifest_path = Path(manifest_path)
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # Validate required fields
        if 'checksums' not in manifest_data:
            raise ValueError("Invalid manifest: missing 'checksums' field")
        
        logger.info(f"Loaded checksum manifest from {manifest_path}")
        return manifest_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
        raise

def verify_file_checksum(
    file_path: str, 
    manifest_path: str,
    expected_checksum: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Verify a single file's checksum against a manifest or expected value.
    
    Args:
        file_path: Path to the file to verify
        manifest_path: Path to the checksum manifest
        expected_checksum: Optional direct checksum to verify against
        
    Returns:
        Tuple of (is_valid, message)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    try:
        # Calculate actual checksum
        actual_checksum = calculate_file_checksum(str(file_path))
        
        if expected_checksum:
            # Direct comparison
            is_valid = actual_checksum == expected_checksum
            msg = "Checksum matches" if is_valid else "Checksum mismatch"
            return is_valid, msg
        
        # Load manifest and find entry
        manifest = load_checksum_manifest(manifest_path)
        
        # Determine relative path from manifest directory
        manifest_dir = Path(manifest_path).parent
        try:
            rel_path = str(file_path.relative_to(manifest_dir))
        except ValueError:
            # File is not under manifest directory, use absolute path
            rel_path = str(file_path)
        
        if rel_path not in manifest['checksums']:
            return False, f"No checksum entry found for {rel_path} in manifest"
        
        expected = manifest['checksums'][rel_path]
        is_valid = actual_checksum == expected
        
        if is_valid:
            return True, "Checksum verified successfully"
        else:
            return False, f"Checksum mismatch: expected {expected[:16]}..., got {actual_checksum[:16]}..."
            
    except Exception as e:
        return False, f"Verification failed: {e}"

def verify_directory_checksum(
    dir_path: str,
    manifest_path: str,
    pattern: Optional[str] = None,
    strict: bool = True
) -> Tuple[bool, Dict[str, str]]:
    """
    Verify all files in a directory against a checksum manifest.
    
    Args:
        dir_path: Path to the directory to verify
        manifest_path: Path to the checksum manifest
        pattern: Optional glob pattern to filter files
        strict: If True, fail if any file is missing or has wrong checksum
        
    Returns:
        Tuple of (all_valid, results_dict) where results_dict maps paths to status messages
    """
    dir_path = Path(dir_path)
    
    if not dir_path.is_dir():
        return False, {"error": f"Path is not a directory: {dir_path}"}
    
    manifest = load_checksum_manifest(manifest_path)
    expected_checksums = manifest['checksums']
    
    results = {}
    all_valid = True
    
    # Check files in manifest
    for rel_path, expected_checksum in expected_checksums.items():
        file_path = dir_path / rel_path
        
        if not file_path.exists():
            results[rel_path] = "MISSING"
            all_valid = False
            if strict:
                return False, results
            continue
        
        try:
            actual_checksum = calculate_file_checksum(str(file_path))
            if actual_checksum == expected_checksum:
                results[rel_path] = "OK"
            else:
                results[rel_path] = "MISMATCH"
                all_valid = False
                if strict:
                    return False, results
        except Exception as e:
            results[rel_path] = f"ERROR: {e}"
            all_valid = False
            if strict:
                return False, results
    
    # Check for extra files not in manifest (optional warning)
    current_files = set()
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            if pattern and not file_path.match(pattern):
                continue
            try:
                rel_path = str(file_path.relative_to(dir_path))
                current_files.add(rel_path)
            except ValueError:
                pass
    
    extra_files = current_files - set(expected_checksums.keys())
    if extra_files:
        logger.warning(f"Found {len(extra_files)} extra files not in manifest")
        for f in extra_files:
            results[f] = "EXTRA (not in manifest)"
    
    return all_valid, results

def verify_manifest_checksums(manifest_path: str) -> bool:
    """
    Verify the integrity of the manifest file itself by checking its own checksum.
    This requires a separate hash of the manifest to be stored alongside it.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        True if manifest is valid, False otherwise
    """
    # For now, this is a placeholder for manifest self-verification
    # In a full implementation, the manifest would include its own checksum
    logger.debug("Manifest self-verification not yet implemented")
    return True

def main():
    """Command-line interface for checksum utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dataset checksum utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Calculate command
    calc_parser = subparsers.add_parser('calculate', help='Calculate checksums')
    calc_parser.add_argument('path', help='File or directory path')
    calc_parser.add_argument('--output', '-o', help='Output manifest file (for directories)')
    calc_parser.add_argument('--pattern', help='Glob pattern for directory scanning')
    calc_parser.add_argument('--no-recursive', action='store_true', help='Do not scan subdirectories')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify checksums')
    verify_parser.add_argument('path', help='File or directory path')
    verify_parser.add_argument('--manifest', '-m', required=True, help='Manifest file path')
    verify_parser.add_argument('--pattern', help='Glob pattern for directory verification')
    verify_parser.add_argument('--no-strict', action='store_true', help='Continue on first error')
    
    args = parser.parse_args()
    
    if args.command == 'calculate':
        path = Path(args.path)
        
        if path.is_file():
            checksum = calculate_file_checksum(str(path))
            print(f"{path.name}: {checksum}")
            
        elif path.is_dir():
            checksums = calculate_directory_checksum(
                str(path),
                pattern=args.pattern,
                recursive=not args.no_recursive
            )
            
            if args.output:
                save_checksum_manifest(checksums, args.output)
                print(f"Manifest saved to {args.output}")
            else:
                for rel_path, checksum in checksums.items():
                    print(f"{rel_path}: {checksum}")
        
        else:
            parser.error(f"Path does not exist: {args.path}")
            
    elif args.command == 'verify':
        path = Path(args.path)
        
        if path.is_file():
            is_valid, msg = verify_file_checksum(str(path), args.manifest)
            print(f"{path.name}: {msg}")
            return 0 if is_valid else 1
            
        elif path.is_dir():
            is_valid, results = verify_directory_checksum(
                str(path),
                args.manifest,
                pattern=args.pattern,
                strict=not args.no_strict
            )
            
            for rel_path, status in results.items():
                print(f"{rel_path}: {status}")
            
            return 0 if is_valid else 1
        
        else:
            parser.error(f"Path does not exist: {args.path}")
    
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    exit(main())