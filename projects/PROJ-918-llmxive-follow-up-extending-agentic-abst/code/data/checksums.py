"""
Data integrity utilities for the llmXive pipeline.

This module provides functions to generate and verify SHA-256 checksums
for raw and processed data files to ensure data integrity during 
ingestion and processing steps.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHECKSUM_FILE = DATA_DIR / "checksums.json"

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksums(directory: Optional[Path] = None, recursive: bool = True) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.
    
    Args:
        directory: Directory to scan. Defaults to data/raw if None.
        recursive: Whether to scan subdirectories.
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    target_dir = directory if directory else RAW_DIR
    if not target_dir.exists():
        print(f"Warning: Directory {target_dir} does not exist. Skipping.")
        return {}
        
    checksums = {}
    files_to_scan = []
    
    if recursive:
        files_to_scan = list(target_dir.rglob("*"))
    else:
        files_to_scan = list(target_dir.glob("*"))
        
    for file_path in files_to_scan:
        if file_path.is_file() and not file_path.name.startswith("."):
            try:
                rel_path = file_path.relative_to(DATA_DIR)
                checksums[str(rel_path)] = calculate_file_hash(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of checksums to save.
        output_path: Path to save the JSON file. Defaults to data/checksums.json.
    """
    path = output_path if output_path else CHECKSUM_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    print(f"Checksums saved to {path}")

def load_checksums(input_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the JSON file. Defaults to data/checksums.json.
        
    Returns:
        Dictionary of stored checksums.
    """
    path = input_path if input_path else CHECKSUM_FILE
    if not path.exists():
        print(f"Warning: Checksum file {path} not found. Returning empty dict.")
        return {}
        
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_checksums(input_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verify current files against stored checksums.
    
    Args:
        input_path: Path to the checksum JSON file.
        
    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    stored = load_checksums(input_path)
    if not stored:
        return True, []
        
    failed_files = []
    
    for rel_path, expected_hash in stored.items():
        full_path = DATA_DIR / rel_path
        if not full_path.exists():
            failed_files.append(f"{rel_path} (MISSING)")
            continue
            
        try:
            current_hash = calculate_file_hash(full_path)
            if current_hash != expected_hash:
                failed_files.append(f"{rel_path} (MISMATCH)")
        except Exception as e:
            failed_files.append(f"{rel_path} (ERROR: {e})")
            
    return len(failed_files) == 0, failed_files

def main():
    """CLI entry point for checksum operations."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate or verify data checksums for llmXive pipeline."
    )
    parser.add_argument(
        "action",
        choices=["generate", "verify", "generate-raw", "generate-processed"],
        help="Action to perform: generate, verify, generate-raw, generate-processed"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output path for checksum file (default: data/checksums.json)"
    )
    
    args = parser.parse_args()
    output_path = Path(args.output) if args.output else None
    
    if args.action == "generate":
        checksums = generate_checksums(DATA_DIR, recursive=True)
        save_checksums(checksums, output_path)
    elif args.action == "generate-raw":
        checksums = generate_checksums(RAW_DIR, recursive=True)
        save_checksums(checksums, output_path)
    elif args.action == "generate-processed":
        checksums = generate_checksums(PROCESSED_DIR, recursive=True)
        save_checksums(checksums, output_path)
    elif args.action == "verify":
        valid, failures = verify_checksums(output_path)
        if valid:
            print("✓ All checksums verified successfully.")
            sys.exit(0)
        else:
            print("✗ Checksum verification failed:")
            for f in failures:
                print(f"  - {f}")
            sys.exit(1)

if __name__ == "__main__":
    main()