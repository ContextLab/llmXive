"""
Checksum utilities for computing and verifying SHA-256 hashes of dataset files.

This module provides functions to:
- Compute SHA-256 checksums for files and directories
- Store checksums in data/checksums.json
- Verify files against stored checksums
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from seeds import get_seed_value


CHECKSUMS_FILE = Path("data/checksums.json")
CHUNK_SIZE = 8192  # Read files in 8KB chunks for memory efficiency


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string representation of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def compute_directory_checksums(
    directory: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.
    
    Args:
        directory: Path to the directory to scan.
        recursive: If True, scan subdirectories recursively.
        extensions: Optional list of file extensions to include (e.g., ['.json', '.csv']).
                   If None, include all files.
                
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path points to a file, not a directory.
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is a file, not a directory: {directory}")
    
    checksums = {}
    
    if recursive:
        files = directory.rglob("*")
    else:
        files = directory.iterdir()
    
    for file_path in files:
        if file_path.is_file():
            # Filter by extension if specified
            if extensions is not None:
                if file_path.suffix not in extensions:
                    continue
            
            # Store relative path for portability
            rel_path = str(file_path.relative_to(directory))
            checksums[rel_path] = compute_sha256(file_path)
    
    return checksums


def write_checksums(
    checksums: Dict[str, str],
    output_path: Optional[Union[str, Path]] = None,
    description: Optional[str] = None
) -> Path:
    """
    Write checksums to a JSON file.
    
    Args:
        checksums: Dictionary mapping file paths to SHA-256 checksums.
        output_path: Path to the output JSON file. Defaults to data/checksums.json.
        description: Optional description of what these checksums represent.
                
    Returns:
        Path to the written checksums file.
    """
    output_path = Path(output_path) if output_path else CHECKSUMS_FILE
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "checksums": checksums,
        "algorithm": "sha256",
        "description": description or "Dataset checksums for integrity verification",
        "seed_value": get_seed_value(),
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    
    return output_path


def read_checksums(
    input_path: Optional[Union[str, Path]] = None
) -> Dict[str, str]:
    """
    Read checksums from a JSON file.
    
    Args:
        input_path: Path to the checksums JSON file. Defaults to data/checksums.json.
                
    Returns:
        Dictionary mapping file paths to their SHA-256 checksums.
        
    Raises:
        FileNotFoundError: If the checksums file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    input_path = Path(input_path) if input_path else CHECKSUMS_FILE
    
    if not input_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("checksums", {})


def verify_checksums(
    base_path: Union[str, Path],
    input_path: Optional[Union[str, Path]] = None,
    strict: bool = True
) -> Dict[str, bool]:
    """
    Verify files against stored checksums.
    
    Args:
        base_path: Base directory path for resolving relative file paths.
        input_path: Path to the checksums JSON file. Defaults to data/checksums.json.
        strict: If True, fail if checksums file is missing. If False, return empty dict.
                
    Returns:
        Dictionary mapping file paths to verification results (True=valid, False=invalid).
        
    Raises:
        FileNotFoundError: If checksums file is missing and strict=True.
    """
    input_path = Path(input_path) if input_path else CHECKSUMS_FILE
    base_path = Path(base_path)
    
    if not input_path.exists():
        if strict:
            raise FileNotFoundError(f"Checksums file not found: {input_path}")
        return {}
    
    stored_checksums = read_checksums(input_path)
    results = {}
    
    for rel_path, expected_hash in stored_checksums.items():
        file_path = base_path / rel_path
        
        if not file_path.exists():
            results[rel_path] = False
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            results[rel_path] = actual_hash == expected_hash
        except Exception:
            results[rel_path] = False
    
    return results


def register_dataset_checksum(
    dataset_name: str,
    file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Register a single dataset file's checksum.
    
    This is a convenience function for the data ingestion pipeline to
    record checksums as datasets are downloaded.
    
    Args:
        dataset_name: Name/identifier for the dataset (e.g., 'code_search_net').
        file_path: Path to the dataset file.
        output_path: Path to the checksums JSON file. Defaults to data/checksums.json.
                
    Returns:
        Path to the updated checksums file.
    """
    file_path = Path(file_path)
    output_path = Path(output_path) if output_path else CHECKSUMS_FILE
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing checksums or create new dict
    checksums = {}
    if output_path.exists():
        try:
            checksums = read_checksums(output_path)
        except (json.JSONDecodeError, KeyError):
            checksums = {}
    
    # Add new checksum
    checksums[str(file_path)] = compute_sha256(file_path)
    
    # Write updated checksums
    write_checksums(
        checksums,
        output_path=output_path,
        description="Dataset checksums for integrity verification"
    )
    
    return output_path


def main():
    """
    Main entry point for checksum utilities.
    
    When run directly, this function demonstrates the checksum utilities
    by computing checksums for files in the data directory.
    """
    import sys
    
    print("Checksum Utilities - T005 Implementation")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if there are any files in data directory to checksum
    data_files = list(data_dir.glob("*"))
    data_files = [f for f in data_files if f.is_file()]
    
    if data_files:
        print(f"\nFound {len(data_files)} file(s) in data/ directory:")
        
        for file_path in data_files:
            try:
                checksum = compute_sha256(file_path)
                print(f"  {file_path.name}: {checksum[:16]}...")
            except Exception as e:
                print(f"  {file_path.name}: ERROR - {e}")
        
        # Write checksums to JSON
        checksums = {}
        for file_path in data_files:
            checksums[str(file_path)] = compute_sha256(file_path)
        
        output_path = write_checksums(checksums)
        print(f"\nChecksums written to: {output_path}")
    else:
        print("\nNo files found in data/ directory.")
        print("Create some dataset files and run again to register checksums.")
    
    # Verify checksums if file exists
    checksums_file = Path("data/checksums.json")
    if checksums_file.exists():
        print(f"\nVerifying checksums in: {checksums_file}")
        results = verify_checksums(".", checksums_file, strict=False)
        
        if results:
            valid_count = sum(1 for v in results.values() if v)
            print(f"  Valid: {valid_count}/{len(results)}")
    
    print("\n" + "=" * 50)
    print("Checksum utilities ready for dataset ingestion pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
