"""
Checksum utilities for raw data integrity verification.

This module provides functions to compute SHA-256 checksums for files and directories,
save/load checksum manifests, and verify data integrity against stored checksums.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        error(f"Error reading file {file_path}: {e}")
        raise

def generate_checksum_for_file(file_path: Path) -> Tuple[Path, str]:
    """
    Generate checksum for a single file and return the path and hash.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Tuple of (file_path, sha256_hash).
    """
    info(f"Generating checksum for: {file_path}")
    checksum = compute_sha256(file_path)
    return file_path, checksum

def compute_checksums_for_directory(directory: Path, recursive: bool = True) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.
    
    Args:
        directory: Path to the directory.
        recursive: If True, include files in subdirectories.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
        
    checksums = {}
    
    if recursive:
        files = [f for f in directory.rglob('*') if f.is_file()]
    else:
        files = [f for f in directory.iterdir() if f.is_file()]
        
    for file_path in files:
        try:
            _, checksum = generate_checksum_for_file(file_path)
            relative_path = str(file_path.relative_to(directory))
            checksums[relative_path] = checksum
            info(f"  Computed: {relative_path}")
        except Exception as e:
            warning(f"Skipping {file_path} due to error: {e}")
            
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path to save the manifest file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "algorithm": "sha256",
        "files": checksums
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        info(f"Checksum manifest saved to: {output_path}")
    except IOError as e:
        error(f"Failed to save checksum manifest: {e}")
        raise

def load_checksums(manifest_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON manifest file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Dictionary of file paths to checksums.
        
    Raises:
        FileNotFoundError: If manifest does not exist.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        if "files" not in manifest:
            raise ValueError("Invalid manifest format: missing 'files' key")
            
        info(f"Loaded {len(manifest['files'])} checksums from: {manifest_path}")
        return manifest["files"]
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in manifest {manifest_path}: {e}")
        raise
    except ValueError as e:
        error(f"Invalid manifest structure: {e}")
        raise

def verify_checksums(
    base_directory: Path, 
    stored_checksums: Dict[str, str], 
    verbose: bool = False
) -> Tuple[bool, List[str]]:
    """
    Verify files against stored checksums.
    
    Args:
        base_directory: Root directory where files are located.
        stored_checksums: Dictionary of relative file paths to expected checksums.
        verbose: If True, log details of verification.
        
    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    all_valid = True
    failed_files = []
    
    for relative_path, expected_checksum in stored_checksums.items():
        file_path = base_directory / relative_path
        
        if not file_path.exists():
            warning(f"File missing during verification: {relative_path}")
            failed_files.append(relative_path)
            all_valid = False
            continue
            
        try:
            actual_checksum = compute_sha256(file_path)
            
            if actual_checksum == expected_checksum:
                if verbose:
                    info(f"  OK: {relative_path}")
            else:
                warning(f"  MISMATCH: {relative_path}")
                warning(f"    Expected: {expected_checksum}")
                warning(f"    Actual:   {actual_checksum}")
                failed_files.append(relative_path)
                all_valid = False
        except Exception as e:
            warning(f"  ERROR reading {relative_path}: {e}")
            failed_files.append(relative_path)
            all_valid = False
            
    return all_valid, failed_files

def main() -> None:
    """
    Main entry point for checksum utility.
    
    Usage:
        python code/checksums.py generate <directory> <output_manifest>
        python code/checksums.py verify <directory> <manifest>
    """
    import sys
    
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python code/checksums.py generate <directory> <output_manifest>")
        print("  python code/checksums.py verify <directory> <manifest>")
        sys.exit(1)
        
    command = sys.argv[1]
    directory = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    
    if command == "generate":
        if not directory.is_dir():
            error(f"Directory not found: {directory}")
            sys.exit(1)
            
        info(f"Generating checksums for: {directory}")
        checksums = compute_checksums_for_directory(directory, recursive=True)
        save_checksums(checksums, output_path)
        info(f"Total files processed: {len(checksums)}")
        
    elif command == "verify":
        if not output_path.is_file():
            error(f"Manifest not found: {output_path}")
            sys.exit(1)
            
        info(f"Verifying checksums for: {directory}")
        stored_checksums = load_checksums(output_path)
        all_valid, failed_files = verify_checksums(directory, stored_checksums, verbose=True)
        
        if all_valid:
            info("✓ All files verified successfully.")
        else:
            error(f"✗ Verification failed for {len(failed_files)} files:")
            for f in failed_files:
                error(f"  - {f}")
            sys.exit(1)
    else:
        error(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()