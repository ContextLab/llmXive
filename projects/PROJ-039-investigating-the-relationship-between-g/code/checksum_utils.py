import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json

logger = logging.getLogger(__name__)

def compute_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def generate_checksums(root_dir: str, output_path: str, algorithm: str = 'sha256') -> Dict[str, str]:
    """
    Generate checksums for all files in a directory tree.
    
    Args:
        root_dir: Root directory to scan.
        output_path: Path to write the checksum file.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to checksums.
    """
    root = Path(root_dir)
    checksums = {}
    
    if not root.exists():
        logger.warning(f"Root directory does not exist: {root_dir}")
        # Create empty file and return
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"# Checksums generated at {root}\n")
            f.write(f"# Algorithm: {algorithm}\n")
        return checksums
        
    for file_path in root.rglob('*'):
        if file_path.is_file():
            try:
                checksum = compute_checksum(str(file_path), algorithm)
                rel_path = file_path.relative_to(root)
                checksums[str(rel_path)] = checksum
                logger.debug(f"Computed checksum for {rel_path}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")
                
    # Write output file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(f"# Checksums generated at {root}\n")
        f.write(f"# Algorithm: {algorithm}\n")
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")
            
    logger.info(f"Generated checksums for {len(checksums)} files in {output_path}")
    return checksums

def verify_checksums(checksum_file_path: str, root_dir: str = None) -> Tuple[bool, List[str]]:
    """
    Verify checksums against a stored checksum file.
    
    Args:
        checksum_file_path: Path to the checksum file.
        root_dir: Root directory to verify against (defaults to parent of checksum file).
        
    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    path = Path(checksum_file_path)
    if not path.exists():
        logger.error(f"Checksum file not found: {checksum_file_path}")
        return False, [checksum_file_path]
        
    if root_dir is None:
        root_dir = str(path.parent)
        
    checksums = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                checksum, rel_path = parts
                checksums[rel_path] = checksum
                
    failed_files = []
    all_valid = True
    
    for rel_path, expected_checksum in checksums.items():
        full_path = Path(root_dir) / rel_path
        if not full_path.exists():
            logger.error(f"File missing: {full_path}")
            failed_files.append(rel_path)
            all_valid = False
            continue
            
        try:
            actual_checksum = compute_checksum(str(full_path))
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}")
                failed_files.append(rel_path)
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            failed_files.append(rel_path)
            all_valid = False
            
    return all_valid, failed_files

def update_checksum_for_file(file_path: str, checksum_file_path: str, algorithm: str = 'sha256') -> bool:
    """
    Update the checksum for a single file in the checksum file.
    If the file is not in the checksum file, it is added.
    
    Args:
        file_path: Path to the file to update.
        checksum_file_path: Path to the checksum file.
        algorithm: Hash algorithm to use.
        
    Returns:
        True if successful, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return False
        
    new_checksum = compute_checksum(str(file_path), algorithm)
    rel_path = str(path)
    
    # Load existing checksums
    checksums = {}
    if Path(checksum_file_path).exists():
        with open(checksum_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    checksums[parts[1]] = parts[0]
                    
    # Update or add
    checksums[rel_path] = new_checksum
    
    # Write back
    Path(checksum_file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file_path, 'w') as f:
        f.write(f"# Checksums updated at {datetime.now().isoformat()}\n")
        f.write(f"# Algorithm: {algorithm}\n")
        for p, c in sorted(checksums.items()):
            f.write(f"{c}  {p}\n")
            
    logger.info(f"Updated checksum for {rel_path}")
    return True

def main():
    """Main entry point for checksum operations."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='Generate and verify checksums for data files.')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate checksums for all files in a directory')
    gen_parser.add_argument('root_dir', help='Root directory to scan')
    gen_parser.add_argument('-o', '--output', default='artifacts/checksums.txt', help='Output checksum file path')
    gen_parser.add_argument('-a', '--algorithm', default='sha256', help='Hash algorithm')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify checksums')
    verify_parser.add_argument('checksum_file', help='Path to checksum file')
    verify_parser.add_argument('-r', '--root', help='Root directory to verify against')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_checksums(args.root_dir, args.output, args.algorithm)
        print(f"Checksums written to {args.output}")
    elif args.command == 'verify':
        valid, failed = verify_checksums(args.checksum_file, args.root)
        if valid:
            print("All checksums verified successfully.")
        else:
            print(f"Verification failed for {len(failed)} files:")
            for f in failed:
                print(f"  - {f}")
            exit(1)
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
