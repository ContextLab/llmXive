"""
Checksum validation module for dataset integrity.

Implements Principle III: Data Integrity via cryptographic checksums.
Provides functions to generate, save, load, and validate checksums for all files
in the data/raw directory.
"""
import json
import hashlib
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from code.dataset.generator import PuzzleInstance

# Constants
CHECKSUM_ALGORITHM = "sha256"
CHECKSUM_MANIFEST_FILE = "checksums.json"
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"

def compute_file_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Compute the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string representation of the checksum
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")
    
    return hasher.hexdigest()

def generate_checksums_for_directory(directory: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory recursively.
    
    Args:
        directory: Path to the directory to process
        
    Returns:
        Dictionary mapping relative file paths to their checksums
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    checksums = {}
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(directory))
            checksum = compute_file_checksum(file_path)
            checksums[relative_path] = checksum
            print(f"  Computed checksum for: {relative_path}")
    
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary of file paths to checksums
        output_path: Path where the manifest should be saved
    """
    manifest = {
        "version": "1.0",
        "algorithm": CHECKSUM_ALGORITHM,
        "generated_at": datetime.utcnow().isoformat(),
        "checksums": checksums
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Checksums saved to: {output_path}")

def load_checksums(manifest_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON manifest file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        Dictionary of file paths to checksums
        
    Raises:
        FileNotFoundError: If the manifest does not exist
        json.JSONDecodeError: If the manifest is invalid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    return manifest.get("checksums", {})

def validate_data_integrity(data_dir: Path, manifest_path: Optional[Path] = None) -> bool:
    """
    Validate the integrity of all files in a directory against stored checksums.
    
    Args:
        data_dir: Path to the data directory to validate
        manifest_path: Optional path to the checksum manifest. If None, uses default location.
        
    Returns:
        True if all files are valid, False otherwise
        
    Raises:
        FileNotFoundError: If the manifest is not found
    """
    if manifest_path is None:
        manifest_path = data_dir.parent / DATA_PROCESSED_DIR / CHECKSUM_MANIFEST_FILE
    
    if not manifest_path.exists():
        print(f"ERROR: Checksum manifest not found at {manifest_path}")
        print("Please run checksum generation first.")
        return False
    
    stored_checksums = load_checksums(manifest_path)
    
    if not stored_checksums:
        print("ERROR: No checksums found in manifest.")
        return False
    
    print(f"Validating {len(stored_checksums)} files...")
    all_valid = True
    valid_count = 0
    invalid_count = 0
    missing_count = 0
    
    for relative_path, expected_checksum in stored_checksums.items():
        file_path = data_dir / relative_path
        
        if not file_path.exists():
            print(f"  MISSING: {relative_path}")
            missing_count += 1
            all_valid = False
            continue
        
        try:
            actual_checksum = compute_file_checksum(file_path)
            
            if actual_checksum == expected_checksum:
                valid_count += 1
            else:
                print(f"  INVALID: {relative_path}")
                print(f"    Expected: {expected_checksum}")
                print(f"    Actual:   {actual_checksum}")
                invalid_count += 1
                all_valid = False
        except Exception as e:
            print(f"  ERROR reading {relative_path}: {e}")
            invalid_count += 1
            all_valid = False
    
    print(f"\nValidation Summary:")
    print(f"  Total files: {len(stored_checksums)}")
    print(f"  Valid:       {valid_count}")
    print(f"  Invalid:     {invalid_count}")
    print(f"  Missing:     {missing_count}")
    
    if all_valid:
        print("  Status: ALL FILES VALID")
    else:
        print("  Status: INTEGRITY CHECK FAILED")
    
    return all_valid

def update_manifest(data_dir: Path, manifest_path: Optional[Path] = None) -> None:
    """
    Update the checksum manifest with current file checksums.
    
    This should be run after any data generation or modification.
    
    Args:
        data_dir: Path to the data directory
        manifest_path: Optional path to the manifest file
    """
    if manifest_path is None:
        manifest_path = data_dir.parent / DATA_PROCESSED_DIR / CHECKSUM_MANIFEST_FILE
    
    print(f"Generating checksums for {data_dir}...")
    checksums = generate_checksums_for_directory(data_dir)
    
    if not checksums:
        print("WARNING: No files found to checksum.")
        return
    
    save_checksums(checksums, manifest_path)
    print(f"Manifest updated successfully.")

def main() -> int:
    """
    Main entry point for checksum validation script.
    
    Usage:
        python code/dataset/validate_checksums.py generate  # Generate checksums
        python code/dataset/validate_checksums.py validate  # Validate integrity
        python code/dataset/validate_checksums.py update    # Update manifest
        
    Returns:
        0 on success, 1 on failure
    """
    if len(sys.argv) < 2:
        print("Usage: python validate_checksums.py <generate|validate|update>")
        print("  generate: Generate checksums for all files in data/raw/")
        print("  validate: Validate integrity of data/raw/ against stored checksums")
        print("  update:   Update the checksum manifest with current file checksums")
        return 1
    
    action = sys.argv[1].lower()
    data_dir = Path(DATA_RAW_DIR)
    
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        print("Please ensure data/raw/ exists and contains puzzle files.")
        return 1
    
    if action == "generate":
        print("Generating checksums for data/raw/...")
        checksums = generate_checksums_for_directory(data_dir)
        
        if not checksums:
            print("WARNING: No files found in data/raw/. Nothing to checksum.")
            return 0
        
        manifest_path = Path(DATA_PROCESSED_DIR) / CHECKSUM_MANIFEST_FILE
        save_checksums(checksums, manifest_path)
        print("Checksum generation complete.")
        return 0
    
    elif action == "validate":
        manifest_path = Path(DATA_PROCESSED_DIR) / CHECKSUM_MANIFEST_FILE
        is_valid = validate_data_integrity(data_dir, manifest_path)
        return 0 if is_valid else 1
    
    elif action == "update":
        update_manifest(data_dir)
        return 0
    
    else:
        print(f"ERROR: Unknown action '{action}'")
        print("Valid actions: generate, validate, update")
        return 1

if __name__ == "__main__":
    sys.exit(main())
