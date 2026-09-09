"""
Utility functions for SHA256 checksum verification and management.
Generates, verifies, and updates checksums for project data files.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def compute_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        raise

def generate_checksums(data_dir: str = 'data', output_path: str = 'artifacts/checksums.txt') -> Dict[str, str]:
    """
    Generate SHA256 checksums for all files in the data directory.

    Args:
        data_dir: Root directory containing data files.
        output_path: Path to write the checksums file.

    Returns:
        Dictionary mapping relative file paths to their checksums.

    Raises:
        FileNotFoundError: If the data directory does not exist.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    if not data_path.is_dir():
        raise ValueError(f"Path is not a directory: {data_dir}")

    checksums = {}
    files_processed = 0

    # Recursively find all files
    for file_path in data_path.rglob('*'):
        if file_path.is_file():
            try:
                # Get relative path from data directory
                relative_path = str(file_path.relative_to(data_path))
                checksum = compute_checksum(str(file_path))
                checksums[relative_path] = checksum
                files_processed += 1
                logger.info(f"Checksummed: {relative_path}")
            except Exception as e:
                logger.warning(f"Failed to checksum {file_path}: {e}")

    if files_processed == 0:
        logger.warning(f"No files found in {data_dir} to checksum.")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write checksums to file
    with open(output_file, 'w') as f:
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")

    logger.info(f"Generated checksums for {files_processed} files in {output_path}")
    return checksums

def verify_checksums(checksum_file: str = 'artifacts/checksums.txt', data_dir: str = 'data') -> Tuple[bool, Dict[str, str]]:
    """
    Verify file integrity against stored checksums.

    Args:
        checksum_file: Path to the checksums file.
        data_dir: Root directory containing data files.

    Returns:
        Tuple of (all_valid, failed_files_dict) where failed_files_dict maps
        relative paths to error messages or 'mismatch'.
    """
    checksum_path = Path(checksum_file)
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")

    # Read stored checksums
    stored_checksums = {}
    with open(checksum_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('  ', 1)
            if len(parts) == 2:
                stored_checksums[parts[1]] = parts[0]

    failed_files = {}
    all_valid = True

    data_path = Path(data_dir)
    for rel_path, expected_checksum in stored_checksums.items():
        file_path = data_path / rel_path
        if not file_path.exists():
            failed_files[rel_path] = "File not found"
            all_valid = False
            continue

        try:
            actual_checksum = compute_checksum(str(file_path))
            if actual_checksum != expected_checksum:
                failed_files[rel_path] = "mismatch"
                all_valid = False
                logger.error(f"Checksum mismatch for {rel_path}")
            else:
                logger.debug(f"Checksum verified: {rel_path}")
        except Exception as e:
            failed_files[rel_path] = str(e)
            all_valid = False
            logger.error(f"Error verifying {rel_path}: {e}")

    if all_valid:
        logger.info(f"All {len(stored_checksums)} files verified successfully.")
    else:
        logger.warning(f"Verification failed for {len(failed_files)} files.")

    return all_valid, failed_files

def update_checksum_for_file(file_path: str, checksum_file: str = 'artifacts/checksums.txt') -> bool:
    """
    Update the checksum for a specific file in the checksums file.

    Args:
        file_path: Path to the file to update.
        checksum_file: Path to the checksums file.

    Returns:
        True if successful, False if file not found in checksums file.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get relative path from data directory
    try:
        rel_path = str(Path(file_path).relative_to('data'))
    except ValueError:
        # If file is not under data/, use absolute path or skip
        logger.warning(f"File {file_path} is not under data/ directory, skipping relative path conversion.")
        rel_path = file_path

    new_checksum = compute_checksum(file_path)

    checksum_path = Path(checksum_file)
    if not checksum_path.exists():
        # Create new checksums file
        with open(checksum_path, 'w') as f:
            f.write(f"{new_checksum}  {rel_path}\n")
        logger.info(f"Created checksums file with {rel_path}")
        return True

    # Read existing checksums
    checksums = {}
    with open(checksum_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('  ', 1)
            if len(parts) == 2:
                checksums[parts[1]] = parts[0]

    # Update or add the checksum
    checksums[rel_path] = new_checksum

    # Write back
    with open(checksum_path, 'w') as f:
        for path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {path}\n")

    logger.info(f"Updated checksum for {rel_path}")
    return True

def main():
    """
    Main entry point for checksum utility.
    Usage:
      - Generate: python code/checksum_utils.py generate [data_dir] [output_file]
      - Verify: python code/checksum_utils.py verify [checksum_file] [data_dir]
      - Update: python code/checksum_utils.py update [file_path] [checksum_file]
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python checksum_utils.py <generate|verify|update> [args...]")
        print("  generate [data_dir] [output_file] - Generate checksums for all files in data_dir")
        print("  verify [checksum_file] [data_dir] - Verify files against checksum_file")
        print("  update [file_path] [checksum_file] - Update checksum for a single file")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'generate':
        data_dir = sys.argv[2] if len(sys.argv) > 2 else 'data'
        output_file = sys.argv[3] if len(len(sys.argv)) > 3 else 'artifacts/checksums.txt'
        try:
            generate_checksums(data_dir, output_file)
            print(f"Checksums generated successfully at {output_file}")
        except Exception as e:
            print(f"Error generating checksums: {e}")
            sys.exit(1)

    elif command == 'verify':
        checksum_file = sys.argv[2] if len(sys.argv) > 2 else 'artifacts/checksums.txt'
        data_dir = sys.argv[3] if len(sys.argv) > 3 else 'data'
        try:
            all_valid, failed = verify_checksums(checksum_file, data_dir)
            if all_valid:
                print("All checksums verified successfully.")
                sys.exit(0)
            else:
                print(f"Verification failed for {len(failed)} files:")
                for path, reason in failed.items():
                    print(f"  - {path}: {reason}")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying checksums: {e}")
            sys.exit(1)

    elif command == 'update':
        if len(sys.argv) < 4:
            print("Usage: python checksum_utils.py update <file_path> [checksum_file]")
            sys.exit(1)
        file_path = sys.argv[2]
        checksum_file = sys.argv[3] if len(sys.argv) > 3 else 'artifacts/checksums.txt'
        try:
            update_checksum_for_file(file_path, checksum_file)
            print(f"Checksum updated for {file_path}")
        except Exception as e:
            print(f"Error updating checksum: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
