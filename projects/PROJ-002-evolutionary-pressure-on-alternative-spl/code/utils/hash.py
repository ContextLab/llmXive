"""
Artifact hashing utilities for the evolutionary pressure pipeline.

Implements FR-009 and SC-005:
- Generate SHA-256 checksums for all intermediate and final files (BAMs, PSI tables, results TSVs).
- Record the hash of external input artifacts (e.g., primate_tree.nwk) in the manifest.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger

# Constants
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for large file hashing
MANIFEST_FILENAME = "artifacts_manifest.json"
HASH_ALGORITHM = "sha256"

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise
    
    return sha256_hash.hexdigest()

def generate_manifest(
    file_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a manifest JSON file containing SHA-256 hashes for a list of files.
    
    Args:
        file_paths: List of file paths to hash.
        output_path: Path where the manifest JSON will be written.
        exclude_patterns: Optional list of glob patterns to exclude from hashing.
        
    Returns:
        The manifest dictionary.
        
    Raises:
        FileNotFoundError: If any file in file_paths does not exist.
        IOError: If the manifest cannot be written.
    """
    manifest = {
        "algorithm": HASH_ALGORITHM,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "files": {}
    }
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for file_path in file_paths:
        file_path = Path(file_path)
        
        # Check exclusions
        if exclude_patterns:
            from fnmatch import fnmatch
            if any(fnmatch(str(file_path), pattern) for pattern in exclude_patterns):
                logger.debug(f"Skipping excluded file: {file_path}")
                continue
        
        if not file_path.exists():
            logger.warning(f"File not found, skipping: {file_path}")
            continue
        
        if file_path.is_dir():
            logger.warning(f"Skipping directory: {file_path}")
            continue
        
        try:
            file_hash = calculate_sha256(file_path)
            manifest["files"][str(file_path)] = file_hash
            logger.debug(f"Hashed {file_path}: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            raise
    
    try:
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write manifest to {output_path}: {e}")
        raise
    
    return manifest

def verify_manifest(manifest_path: Union[str, Path]) -> bool:
    """
    Verify the integrity of files against a manifest.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        True if all files match their hashes, False otherwise.
        
    Raises:
        FileNotFoundError: If the manifest or any listed file is missing.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    manifest_path = Path(manifest_path)
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
        raise
    
    all_valid = True
    
    for file_path_str, expected_hash in manifest.get("files", {}).items():
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            logger.error(f"File missing during verification: {file_path}")
            all_valid = False
            continue
        
        try:
            actual_hash = calculate_sha256(file_path)
            if actual_hash != expected_hash:
                logger.error(
                    f"Hash mismatch for {file_path}\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Actual:   {actual_hash}"
                )
                all_valid = False
            else:
                logger.debug(f"Verified {file_path}: OK")
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False
    
    if all_valid:
        logger.info("Manifest verification: ALL PASSED")
    else:
        logger.warning("Manifest verification: FAILED")
    
    return all_valid

def log_hash_to_file(
    file_path: Union[str, Path],
    log_path: Union[str, Path],
    description: Optional[str] = None
) -> str:
    """
    Calculate a file's hash and append it to a log file.
    
    Args:
        file_path: Path to the file to hash.
        log_path: Path to the log file.
        description: Optional description of the file.
        
    Returns:
        The calculated hash.
    """
    file_path = Path(file_path)
    log_path = Path(log_path)
    
    file_hash = calculate_sha256(file_path)
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    desc_str = f" ({description})" if description else ""
    log_entry = f"[{timestamp}] HASH{desc_str}: {file_path} -> {file_hash}\n"
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(log_entry)
    
    logger.info(f"Logged hash for {file_path}")
    return file_hash

def log_manifest_entry(
    manifest_path: Union[str, Path],
    file_path: Union[str, Path],
    description: Optional[str] = None
) -> str:
    """
    Calculate a file's hash and append a single entry to an existing manifest.
    If the manifest does not exist, create it.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        file_path: Path to the file to hash.
        description: Optional description to store in metadata.
        
    Returns:
        The calculated hash.
    """
    manifest_path = Path(manifest_path)
    file_path = Path(file_path)
    
    file_hash = calculate_sha256(file_path)
    
    manifest = {
        "algorithm": HASH_ALGORITHM,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "files": {}
    }
    
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                existing = json.load(f)
                manifest["files"] = existing.get("files", {})
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing manifest, starting fresh: {e}")
    
    entry = {
        "path": str(file_path),
        "hash": file_hash,
        "description": description,
        "recorded_at": datetime.utcnow().isoformat() + "Z"
    }
    
    manifest["files"][str(file_path)] = file_hash
    
    # Optionally store metadata in a separate key if needed, 
    # but for strict hash verification, the dict of path->hash is primary.
    # We'll keep the simple path->hash structure for verification compatibility.
    
    try:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Updated manifest at {manifest_path}")
    except IOError as e:
        logger.error(f"Failed to update manifest: {e}")
        raise
    
    return file_hash

from datetime import datetime

def main():
    """
    CLI entry point for hash utilities.
    
    Usage:
        python -m code.utils.hash --hash <file>
        python -m code.utils.hash --manifest <list_of_files> --output <output.json>
        python -m code.utils.hash --verify <manifest.json>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Artifact Hashing Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Hash command
    hash_parser = subparsers.add_parser("hash", help="Calculate SHA-256 of a file")
    hash_parser.add_argument("file", type=str, help="File to hash")
    
    # Manifest command
    manifest_parser = subparsers.add_parser("manifest", help="Generate manifest from file list")
    manifest_parser.add_argument("files", nargs="+", type=str, help="Files to include")
    manifest_parser.add_argument("--output", "-o", type=str, required=True, help="Output manifest path")
    manifest_parser.add_argument("--exclude", nargs="*", type=str, help="Patterns to exclude")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify files against manifest")
    verify_parser.add_argument("manifest", type=str, help="Manifest file to verify")
    
    args = parser.parse_args()
    
    if args.command == "hash":
        try:
            h = calculate_sha256(args.file)
            print(f"SHA256: {h}")
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            exit(1)
            
    elif args.command == "manifest":
        try:
            generate_manifest(args.files, args.output, args.exclude)
        except Exception as e:
            logger.error(f"Manifest generation failed: {e}")
            exit(1)
            
    elif args.command == "verify":
        try:
            success = verify_manifest(args.manifest)
            exit(0 if success else 1)
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            exit(1)
    else:
        parser.print_help()
        exit(1)

if __name__ == "__main__":
    main()