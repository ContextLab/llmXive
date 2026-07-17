"""
SHA-256 Checksum Validation Utility for Data Integrity (SC-004).

This module provides functions to calculate, generate, and validate SHA-256 checksums
for data files to ensure integrity during the pipeline execution.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logger
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum calculation: {file_path}")
    
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except PermissionError as e:
        logger.error(f"Permission denied reading file for checksum: {file_path}")
        raise PermissionError(f"Cannot read file: {file_path}") from e

def generate_checksums(file_paths: List[str], output_path: Optional[str] = None) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for a list of files.

    Args:
        file_paths: List of file paths to hash.
        output_path: Optional path to save the checksums as JSON.

    Returns:
        Dictionary mapping file paths to their SHA-256 checksums.
    """
    checksums = {}
    for file_path in file_paths:
        try:
            checksum = calculate_sha256(file_path)
            checksums[file_path] = checksum
            logger.info(f"Generated checksum for {file_path}: {checksum[:16]}...")
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Skipping {file_path} due to error: {e}")
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksums saved to {output_path}")
    
    return checksums

def validate_checksums(
    file_paths: List[str], 
    expected_checksums: Optional[Dict[str, str]] = None, 
    checksum_file: Optional[str] = None
) -> Tuple[Dict[str, bool], Dict[str, str], Dict[str, str]]:
    """
    Validate files against expected SHA-256 checksums.

    Args:
        file_paths: List of file paths to validate.
        expected_checksums: Optional dictionary of {file_path: expected_hash}.
        checksum_file: Optional path to a JSON file containing expected checksums.

    Returns:
        Tuple of (validation_results, calculated_checksums, errors)
        - validation_results: {file_path: True/False}
        - calculated_checksums: {file_path: actual_hash}
        - errors: {file_path: error_message}
    """
    validation_results = {}
    calculated_checksums = {}
    errors = {}

    # Load expected checksums if provided via file
    if checksum_file and not expected_checksums:
        if not Path(checksum_file).exists():
            raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
        with open(checksum_file, 'r') as f:
            expected_checksums = json.load(f)

    if not expected_checksums:
        logger.warning("No expected checksums provided. Cannot validate.")
        return validation_results, calculated_checksums, errors

    for file_path in file_paths:
        try:
            actual_hash = calculate_sha256(file_path)
            calculated_checksums[file_path] = actual_hash
            
            if file_path in expected_checksums:
                expected_hash = expected_checksums[file_path]
                if actual_hash == expected_hash:
                    validation_results[file_path] = True
                    logger.info(f"Checksum valid for {file_path}")
                else:
                    validation_results[file_path] = False
                    errors[file_path] = f"Mismatch: expected {expected_hash}, got {actual_hash}"
                    logger.error(f"Checksum mismatch for {file_path}")
            else:
                logger.warning(f"No expected checksum for {file_path}, skipping validation")
                validation_results[file_path] = False
                errors[file_path] = "No expected checksum provided"
                
        except Exception as e:
            errors[file_path] = str(e)
            logger.error(f"Error validating {file_path}: {e}")
            validation_results[file_path] = False

    return validation_results, calculated_checksums, errors

def main():
    """
    CLI entry point for checksum utility.
    Usage:
      python code/checksum_utils.py generate <file1> <file2> ... --output <checksums.json>
      python code/checksum_utils.py validate <file1> <file2> ... --checksums <checksums.json>
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  generate: python code/checksum_utils.py generate <file1> [file2] ... --output <output.json>")
        print("  validate: python code/checksum_utils.py validate <file1> [file2] ... --checksums <checksums.json>")
        sys.exit(1)

    command = sys.argv[1]
    files = [f for f in sys.argv[2:] if not f.startswith('--')]
    
    if command == 'generate':
        output_path = None
        for i, arg in enumerate(sys.argv):
            if arg == '--output' and i + 1 < len(sys.argv):
                output_path = sys.argv[i + 1]
                break
        
        if not files:
            print("Error: No files specified for generation.")
            sys.exit(1)
        
        checksums = generate_checksums(files, output_path)
        if not output_path:
            print(json.dumps(checksums, indent=2))
            
    elif command == 'validate':
        checksum_file = None
        for i, arg in enumerate(sys.argv):
            if arg == '--checksums' and i + 1 < len(sys.argv):
                checksum_file = sys.argv[i + 1]
                break
        
        if not files:
            print("Error: No files specified for validation.")
            sys.exit(1)
        
        if not checksum_file:
            print("Error: --checksums file required for validation.")
            sys.exit(1)
        
        try:
            valid, calculated, errors = validate_checksums(files, checksum_file=checksum_file)
            print(f"Validation Results:")
            for path, is_valid in valid.items():
                status = "PASS" if is_valid else "FAIL"
                print(f"  {path}: {status}")
            
            if errors:
                print("\nErrors:")
                for path, msg in errors.items():
                    print(f"  {path}: {msg}")
            
            # Exit with error code if any validation failed
            if not all(valid.values()):
                sys.exit(1)
                
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
