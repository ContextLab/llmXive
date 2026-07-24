"""
SHA-256 Checksum Validation Utility for Data Integrity (SC-004).

Provides functions to calculate, generate, and validate SHA-256 checksums
for data files to ensure integrity during download and processing.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB)
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def generate_checksums(file_paths: List[str], output_path: Optional[str] = None) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for multiple files.
    
    Args:
        file_paths: List of file paths to hash
        output_path: Optional path to write checksums JSON file
        
    Returns:
        Dictionary mapping file paths to their SHA-256 checksums
        
    Raises:
        FileNotFoundError: If any file does not exist
    """
    checksums = {}
    missing_files = []
    
    for file_path in file_paths:
        try:
            checksum = calculate_sha256(file_path)
            checksums[file_path] = checksum
            logger.info(f"Generated checksum for {file_path}: {checksum[:16]}...")
        except FileNotFoundError:
            missing_files.append(file_path)
            logger.warning(f"File not found, skipping: {file_path}")
        except IOError as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    if missing_files:
        logger.warning(f"Skipped {len(missing_files)} missing files")
        
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksums saved to {output_path}")
        
    return checksums


def validate_checksums(checksums: Dict[str, str], strict: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Validate files against a dictionary of expected checksums.
    
    Args:
        checksums: Dictionary mapping file paths to expected checksums
        strict: If True, fail if any file is missing or mismatched
        
    Returns:
        Tuple of (all_valid, valid_files, invalid_files)
        - all_valid: True if all files match their checksums
        - valid_files: List of files that passed validation
        - invalid_files: List of files that failed validation or are missing
        
    Raises:
        FileNotFoundError: If strict=True and any file is missing
    """
    valid_files = []
    invalid_files = []
    all_valid = True
    
    for file_path, expected_checksum in checksums.items():
        if not Path(file_path).exists():
            invalid_files.append(file_path)
            logger.error(f"File missing: {file_path}")
            all_valid = False
            if strict:
                raise FileNotFoundError(f"File missing: {file_path}")
            continue
            
        try:
            actual_checksum = calculate_sha256(file_path)
            if actual_checksum == expected_checksum:
                valid_files.append(file_path)
                logger.info(f"Checksum valid: {file_path}")
            else:
                invalid_files.append(file_path)
                logger.error(f"Checksum mismatch for {file_path}: "
                           f"expected {expected_checksum[:16]}..., "
                           f"got {actual_checksum[:16]}...")
                all_valid = False
        except IOError as e:
            invalid_files.append(file_path)
            logger.error(f"Error validating {file_path}: {e}")
            all_valid = False
            
    return all_valid, valid_files, invalid_files


def load_checksums(checksum_file: str) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        checksum_file: Path to the JSON file containing checksums
        
    Returns:
        Dictionary mapping file paths to checksums
        
    Raises:
        FileNotFoundError: If the checksum file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(checksum_file)
    if not path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
        
    with open(path, 'r') as f:
        return json.load(f)


def main():
    """
    Command-line interface for checksum operations.
    
    Usage:
        python checksum_utils.py generate <file1> [file2 ...] --output <checksums.json>
        python checksum_utils.py validate <checksums.json>
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python checksum_utils.py <generate|validate> [options]")
        print("  generate <file1> [file2 ...] --output <checksums.json>")
        print("  validate <checksums.json>")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "generate":
        files = []
        output = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--output" and i + 1 < len(sys.argv):
                output = sys.argv[i + 1]
                i += 2
            else:
                files.append(sys.argv[i])
                i += 1
                
        if not files:
            print("Error: No files specified for generation")
            sys.exit(1)
            
        checksums = generate_checksums(files, output)
        print(f"Generated {len(checksums)} checksums")
        
    elif command == "validate":
        if len(sys.argv) < 3:
            print("Error: No checksum file specified")
            sys.exit(1)
            
        checksum_file = sys.argv[2]
        try:
            checksums = load_checksums(checksum_file)
            all_valid, valid, invalid = validate_checksums(checksums, strict=True)
            if all_valid:
                print(f"All {len(valid)} files validated successfully")
            else:
                print(f"Validation failed for {len(invalid)} files")
                sys.exit(1)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
