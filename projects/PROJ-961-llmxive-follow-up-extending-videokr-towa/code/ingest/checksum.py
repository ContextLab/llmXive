"""
Checksum verification module for raw data integrity.

This module provides functionality to compute and verify SHA-256 checksums
for raw data artifacts, ensuring data integrity throughout the pipeline.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config
from utils.versioning import compute_sha256


def verify_raw_data_integrity(
    file_path: Union[str, Path],
    expected_checksum: Optional[str] = None,
    checksum_file: Optional[Union[str, Path]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify the integrity of a raw data file using SHA-256 checksums.
    
    Args:
        file_path: Path to the raw data file to verify.
        expected_checksum: Optional expected SHA-256 checksum. If provided,
                           the function will compare against this value.
        checksum_file: Optional path to a JSON file containing known checksums.
                       If provided and expected_checksum is None, the function
                       will look up the checksum from this file.
    
    Returns:
        Tuple of (is_valid, computed_checksum, status_message)
        - is_valid: True if verification passed, False otherwise
        - computed_checksum: The SHA-256 hash of the file
        - status_message: Human-readable status description
    
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If no expected checksum is provided and cannot be loaded
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    
    # Compute the SHA-256 checksum of the file
    computed_checksum = compute_sha256(file_path)
    
    # Determine expected checksum
    if expected_checksum is None:
        if checksum_file:
            checksum_file = Path(checksum_file)
            if checksum_file.exists():
                with open(checksum_file, 'r', encoding='utf-8') as f:
                    checksums = json.load(f)
                filename = file_path.name
                if filename in checksums:
                    expected_checksum = checksums[filename]
                else:
                    raise ValueError(
                        f"No checksum found for '{filename}' in {checksum_file}"
                    )
            else:
                raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
        else:
            raise ValueError(
                "No expected checksum provided and no checksum file specified"
            )
    
    # Verify the checksum
    is_valid = computed_checksum.lower() == expected_checksum.lower()
    
    if is_valid:
        status_message = f"Checksum verified successfully for {file_path.name}"
    else:
        status_message = (
            f"Checksum mismatch for {file_path.name}. "
            f"Expected: {expected_checksum}, Got: {computed_checksum}"
        )
    
    return is_valid, computed_checksum, status_message


def generate_checksum_file(
    data_directory: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    recursive: bool = False
) -> Dict[str, str]:
    """
    Generate a JSON file containing SHA-256 checksums for all files in a directory.
    
    Args:
        data_directory: Path to the directory containing data files.
        output_file: Optional path for the output JSON file. If None,
                    defaults to data/checksums.json.
        recursive: If True, process subdirectories recursively.
    
    Returns:
        Dictionary mapping filenames to their SHA-256 checksums.
    """
    data_directory = Path(data_directory)
    
    if not data_directory.exists():
        raise FileNotFoundError(f"Data directory not found: {data_directory}")
    
    if not data_directory.is_dir():
        raise ValueError(f"Path is not a directory: {data_directory}")
    
    checksums = {}
    
    if recursive:
        files = list(data_directory.rglob('*'))
    else:
        files = list(data_directory.glob('*'))
    
    for file_path in files:
        if file_path.is_file():
            checksum = compute_sha256(file_path)
            # Store relative path from data_directory as key
            relative_path = str(file_path.relative_to(data_directory))
            checksums[relative_path] = checksum
    
    # Write to output file
    if output_file is None:
        output_file = get_path("data/checksums.json")
    
    output_file = Path(output_file)
    ensure_dir(output_file.parent)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    
    return checksums


def verify_all_raw_data(
    data_directory: Union[str, Path],
    checksum_file: Optional[Union[str, Path]] = None
) -> Dict[str, Dict[str, Union[bool, str]]]:
    """
    Verify integrity of all files in a data directory against known checksums.
    
    Args:
        data_directory: Path to the directory containing data files.
        checksum_file: Optional path to the checksum file. If None,
                      defaults to data/checksums.json.
    
    Returns:
        Dictionary mapping filenames to verification results:
        {
            "filename": {
                "valid": bool,
                "status": str,
                "expected": str,
                "computed": str
            }
        }
    """
    data_directory = Path(data_directory)
    
    if not checksum_file:
        checksum_file = get_path("data/checksums.json")
    
    checksum_file = Path(checksum_file)
    
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    with open(checksum_file, 'r', encoding='utf-8') as f:
        checksums = json.load(f)
    
    results = {}
    
    for relative_path, expected_checksum in checksums.items():
        file_path = data_directory / relative_path
        
        if not file_path.exists():
            results[relative_path] = {
                "valid": False,
                "status": "File not found",
                "expected": expected_checksum,
                "computed": None
            }
            continue
        
        try:
            is_valid, computed_checksum, status = verify_raw_data_integrity(
                file_path,
                expected_checksum=expected_checksum
            )
            
            results[relative_path] = {
                "valid": is_valid,
                "status": status,
                "expected": expected_checksum,
                "computed": computed_checksum
            }
        except Exception as e:
            results[relative_path] = {
                "valid": False,
                "status": f"Error: {str(e)}",
                "expected": expected_checksum,
                "computed": None
            }
    
    return results


def main():
    """
    Command-line interface for checksum verification.
    
    Usage:
        python code/ingest/checksum.py verify <file_path> [--expected <checksum>] [--checksum-file <path>]
        python code/ingest/checksum.py generate <data_directory> [--output <path>] [--recursive]
        python code/ingest/checksum.py verify-all <data_directory> [--checksum-file <path>]
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code/ingest/checksum.py <command> [options]")
        print("Commands:")
        print("  verify <file_path> [--expected <checksum>] [--checksum-file <path>]")
        print("  generate <data_directory> [--output <path>] [--recursive]")
        print("  verify-all <data_directory> [--checksum-file <path>]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "verify":
        if len(sys.argv) < 3:
            print("Error: File path required for verify command")
            sys.exit(1)
        
        file_path = sys.argv[2]
        expected_checksum = None
        checksum_file = None
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--expected" and i + 1 < len(sys.argv):
                expected_checksum = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--checksum-file" and i + 1 < len(sys.argv):
                checksum_file = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        try:
            is_valid, computed_checksum, status = verify_raw_data_integrity(
                file_path,
                expected_checksum=expected_checksum,
                checksum_file=checksum_file
            )
            print(status)
            print(f"Computed checksum: {computed_checksum}")
            sys.exit(0 if is_valid else 1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Error: Data directory required for generate command")
            sys.exit(1)
        
        data_directory = sys.argv[2]
        output_file = None
        recursive = False
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--output" and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--recursive":
                recursive = True
                i += 1
            else:
                i += 1
        
        try:
            checksums = generate_checksum_file(
                data_directory,
                output_file=output_file,
                recursive=recursive
            )
            print(f"Generated checksums for {len(checksums)} files")
            if output_file:
                print(f"Output written to: {output_file}")
            else:
                print(f"Output written to: data/checksums.json")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "verify-all":
        if len(sys.argv) < 3:
            print("Error: Data directory required for verify-all command")
            sys.exit(1)
        
        data_directory = sys.argv[2]
        checksum_file = None
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--checksum-file" and i + 1 < len(sys.argv):
                checksum_file = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        try:
            results = verify_all_raw_data(data_directory, checksum_file=checksum_file)
            
            passed = sum(1 for r in results.values() if r["valid"])
            failed = len(results) - passed
            
            print(f"Verification complete: {passed} passed, {failed} failed")
            
            for filename, result in results.items():
                status = "✓" if result["valid"] else "✗"
                print(f"{status} {filename}: {result['status']}")
            
            sys.exit(0 if failed == 0 else 1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()