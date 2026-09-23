import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json

logger = logging.getLogger(__name__)

def compute_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default 'sha256').

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def generate_checksums(data_root: Path, output_path: Path, algorithm: str = 'sha256') -> Dict[str, str]:
    """
    Generate checksums for all files in the data directory and write to a file.

    Args:
        data_root: Root directory of the data to checksum.
        output_path: Path to the output checksum file.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if not data_root.exists():
        raise FileNotFoundError(f"Data root directory not found: {data_root}")
    
    checksums = {}
    files_processed = 0
    
    logger.info(f"Generating checksums for files in {data_root}")
    
    for root, _, files in os.walk(data_root):
        for file_name in files:
            file_path = Path(root) / file_name
            relative_path = file_path.relative_to(data_root)
            
            try:
                checksum = compute_checksum(file_path, algorithm)
                checksums[str(relative_path)] = checksum
                files_processed += 1
                logger.debug(f"Computed checksum for {relative_path}")
            except Exception as e:
                logger.warning(f"Skipping {relative_path} due to error: {e}")
    
    # Write checksums to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")
    
    logger.info(f"Generated checksums for {files_processed} files. Output written to {output_path}")
    return checksums

def verify_checksums(checksum_file: Path, data_root: Path) -> Tuple[bool, List[str]]:
    """
    Verify file checksums against a stored checksum file.

    Args:
        checksum_file: Path to the file containing stored checksums.
        data_root: Root directory of the data to verify.

    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    if not data_root.exists():
        raise FileNotFoundError(f"Data root directory not found: {data_root}")
    
    stored_checksums = {}
    with open(checksum_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: "checksum  relative_path"
            parts = line.split('  ', 1)
            if len(parts) == 2:
                stored_checksums[parts[1]] = parts[0]
            else:
                logger.warning(f"Malformed checksum line: {line}")
    
    failed_files = []
    all_valid = True
    
    logger.info(f"Verifying checksums from {checksum_file}")
    
    for rel_path, expected_checksum in stored_checksums.items():
        file_path = data_root / rel_path
        
        if not file_path.exists():
            logger.error(f"File missing during verification: {rel_path}")
            failed_files.append(rel_path)
            all_valid = False
            continue
        
        try:
            actual_checksum = compute_checksum(file_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {rel_path}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Actual:   {actual_checksum}")
                failed_files.append(rel_path)
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            failed_files.append(rel_path)
            all_valid = False
    
    if all_valid:
        logger.info(f"All {len(stored_checksums)} files verified successfully.")
    else:
        logger.error(f"Verification failed for {len(failed_files)} files.")
    
    return all_valid, failed_files

def update_checksum_for_file(file_path: Path, checksum_file: Path, algorithm: str = 'sha256') -> bool:
    """
    Update the checksum for a single file in the checksum file.
    If the file is not in the checksum file, it is added.

    Args:
        file_path: Path to the file to update.
        checksum_file: Path to the checksum file.
        algorithm: Hash algorithm to use.

    Returns:
        True if update was successful.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Compute new checksum
    new_checksum = compute_checksum(file_path, algorithm)
    
    # Read existing checksums
    stored_checksums = {}
    if checksum_file.exists():
        with open(checksum_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('  ', 1)
                if len(parts) == 2:
                    stored_checksums[parts[1]] = parts[0]
    
    # Update or add the checksum
    relative_path = str(file_path)
    stored_checksums[relative_path] = new_checksum
    
    # Write back
    with open(checksum_file, 'w', encoding='utf-8') as f:
        for rel_path, checksum in sorted(stored_checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")
    
    logger.info(f"Updated checksum for {relative_path}")
    return True

def main():
    """
    Main entry point for checksum utility.
    Usage:
      python checksum_utils.py generate [data_root] [output_path]
      python checksum_utils.py verify [checksum_file] [data_root]
      python checksum_utils.py update [file_path] [checksum_file]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Checksum verification utility")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate checksums for all files in data/')
    gen_parser.add_argument('data_root', nargs='?', default='data', help='Root directory of data (default: data)')
    gen_parser.add_argument('output_path', nargs='?', default='artifacts/checksums.txt', help='Output file path (default: artifacts/checksums.txt)')

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify checksums')
    verify_parser.add_argument('checksum_file', nargs='?', default='artifacts/checksums.txt', help='Checksum file path (default: artifacts/checksums.txt)')
    verify_parser.add_argument('data_root', nargs='?', default='data', help='Root directory of data (default: data)')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update checksum for a single file')
    update_parser.add_argument('file_path', help='Path to the file to update')
    update_parser.add_argument('checksum_file', nargs='?', default='artifacts/checksums.txt', help='Checksum file path (default: artifacts/checksums.txt)')

    args = parser.parse_args()

    if args.command == 'generate':
        data_root = Path(args.data_root)
        output_path = Path(args.output_path)
        try:
            generate_checksums(data_root, output_path)
        except Exception as e:
            logger.error(f"Failed to generate checksums: {e}")
            exit(1)
    elif args.command == 'verify':
        checksum_file = Path(args.checksum_file)
        data_root = Path(args.data_root)
        try:
            all_valid, failed = verify_checksums(checksum_file, data_root)
            exit(0 if all_valid else 1)
        except Exception as e:
            logger.error(f"Failed to verify checksums: {e}")
            exit(1)
    elif args.command == 'update':
        file_path = Path(args.file_path)
        checksum_file = Path(args.checksum_file)
        try:
            update_checksum_for_file(file_path, checksum_file)
        except Exception as e:
            logger.error(f"Failed to update checksum: {e}")
            exit(1)
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
