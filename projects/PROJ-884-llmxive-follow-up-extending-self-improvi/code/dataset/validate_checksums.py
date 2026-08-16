"""
Checksum validation utilities for dataset integrity (Principle III).

This module provides functions to compute, store, load, and validate
SHA-256 checksums for all files in the data/raw/ directory.
"""
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from code.dataset.generator import PuzzleInstance
import os

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hex digest of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def generate_checksums_for_directory(directory: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.
    
    Args:
        directory: Path to the directory containing files
        
    Returns:
        Dictionary mapping relative file paths to their checksums
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    checksums = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(directory))
            checksums[rel_path] = compute_file_checksum(file_path)
    
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary of file paths to checksums
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

def load_checksums(manifest_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON manifest file.
    
    Args:
        manifest_path: Path to the JSON manifest file
        
    Returns:
        Dictionary of file paths to checksums
        
    Raises:
        FileNotFoundError: If the manifest file does not exist
        json.JSONDecodeError: If the manifest is invalid JSON
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_data_integrity(raw_dir: Path, manifest_path: Path) -> Dict[str, Any]:
    """
    Validate data integrity by comparing current checksums to stored manifest.
    
    Args:
        raw_dir: Path to the raw data directory
        manifest_path: Path to the checksum manifest file
        
    Returns:
        Dictionary with validation results including:
        - 'valid': bool indicating if all files match
        - 'missing_files': list of files in manifest but not on disk
        - 'new_files': list of files on disk but not in manifest
        - 'corrupted_files': list of files with mismatched checksums
        - 'total_files_checked': number of files validated
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")
    
    stored_checksums = load_checksums(manifest_path)
    current_checksums = generate_checksums_for_directory(raw_dir)
    
    missing_files = []
    new_files = []
    corrupted_files = []
    
    # Check for missing files (in manifest but not on disk)
    for rel_path in stored_checksums:
        file_path = raw_dir / rel_path
        if not file_path.exists():
            missing_files.append(rel_path)
        else:
            current = current_checksums.get(rel_path)
            stored = stored_checksums[rel_path]
            if current != stored:
                corrupted_files.append(rel_path)
    
    # Check for new files (on disk but not in manifest)
    for rel_path in current_checksums:
        if rel_path not in stored_checksums:
            new_files.append(rel_path)
    
    is_valid = (
        len(missing_files) == 0 and
        len(new_files) == 0 and
        len(corrupted_files) == 0
    )
    
    return {
        "valid": is_valid,
        "missing_files": missing_files,
        "new_files": new_files,
        "corrupted_files": corrupted_files,
        "total_files_checked": len(stored_checksums)
    }

def update_manifest(raw_dir: Path, manifest_path: Path) -> None:
    """
    Update the checksum manifest with current file checksums.
    
    Args:
        raw_dir: Path to the raw data directory
        manifest_path: Path to the manifest file to update
    """
    checksums = generate_checksums_for_directory(raw_dir)
    save_checksums(checksums, manifest_path)

def main() -> int:
    """
    Main entry point for checksum validation.
    
    This script:
    1. Checks if a manifest exists for data/raw/
    2. If not, generates a new manifest
    3. Validates all files against the manifest
    4. Reports results to stdout
    
    Returns:
        0 if validation passes, 1 if validation fails
    """
    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    manifest_path = project_root / "data" / "processed" / "data_checksums.json"
    
    print(f"Scanning directory: {raw_dir}")
    
    if not raw_dir.exists():
        print(f"ERROR: Raw data directory not found: {raw_dir}")
        return 1
    
    files_count = len(list(raw_dir.rglob("*")))
    if files_count == 0:
        print("WARNING: No files found in raw directory.")
        return 0
    
    if not manifest_path.exists():
        print(f"Manifest not found at {manifest_path}. Generating new manifest...")
        update_manifest(raw_dir, manifest_path)
        print(f"Manifest created with checksums for all files.")
        return 0
    
    print(f"Validating integrity against manifest: {manifest_path}")
    try:
        result = validate_data_integrity(raw_dir, manifest_path)
        
        if result["valid"]:
            print("✅ Data integrity validation PASSED.")
            print(f"   Checked {result['total_files_checked']} files.")
            return 0
        else:
            print("❌ Data integrity validation FAILED.")
            
            if result["missing_files"]:
                print(f"   Missing files ({len(result['missing_files'])}):")
                for f in result["missing_files"]:
                    print(f"     - {f}")
            
            if result["new_files"]:
                print(f"   New files ({len(result['new_files'])}):")
                for f in result["new_files"]:
                    print(f"     - {f}")
            
            if result["corrupted_files"]:
                print(f"   Corrupted files ({len(result['corrupted_files'])}):")
                for f in result["corrupted_files"]:
                    print(f"     - {f}")
            
            return 1
            
    except Exception as e:
        print(f"ERROR during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
