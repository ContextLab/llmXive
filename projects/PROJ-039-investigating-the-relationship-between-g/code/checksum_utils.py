"""
Checksum utilities for data integrity verification.
Implements MD5/SHA256 verification to enforce the artifacts/checksums.txt protocol.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from config import get_project_root

logger = logging.getLogger(__name__)

CHECKSUM_FILE = "artifacts/checksums.txt"

def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm (md5 or sha256).
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use ('md5' or 'sha256').
        
    Returns:
        Hexadecimal digest string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    if algorithm.lower() == "md5":
        hasher = hashlib.md5()
    elif algorithm.lower() == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'md5' or 'sha256'.")
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def generate_checksums(files: List[Path], algorithm: str = "sha256") -> Dict[str, str]:
    """
    Generate checksums for a list of files.
    
    Args:
        files: List of file paths to checksum.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    for file_path in files:
        try:
            checksum = compute_checksum(file_path, algorithm)
            rel_path = str(file_path.relative_to(get_project_root()))
            checksums[rel_path] = checksum
            logger.info(f"Generated {algorithm} checksum for {rel_path}: {checksum}")
        except FileNotFoundError as e:
            logger.warning(f"Skipping {file_path}: {e}")
    return checksums

def verify_checksums(checksum_file: Optional[Path] = None, algorithm: str = "sha256") -> Tuple[bool, List[str]]:
    """
    Verify files against a stored checksum file.
    
    Args:
        checksum_file: Path to the checksums.txt file. Defaults to artifacts/checksums.txt.
        algorithm: Hash algorithm expected in the file.
        
    Returns:
        Tuple of (all_valid: bool, failed_files: List[str]).
    """
    if checksum_file is None:
        checksum_file = get_project_root() / CHECKSUM_FILE
    
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False, ["Checksum file missing"]
    
    # Parse stored checksums
    stored_checksums = {}
    with open(checksum_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                # Format: <checksum>  <relative_path>
                stored_checksums[parts[1]] = parts[0]
    
    failed_files = []
    all_valid = True
    
    for rel_path, expected_checksum in stored_checksums.items():
        full_path = get_project_root() / rel_path
        if not full_path.exists():
            logger.error(f"File missing for verification: {rel_path}")
            failed_files.append(rel_path)
            all_valid = False
            continue
        
        try:
            actual_checksum = compute_checksum(full_path, algorithm)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}")
                failed_files.append(rel_path)
                all_valid = False
            else:
                logger.info(f"Checksum OK: {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            failed_files.append(rel_path)
            all_valid = False
    
    return all_valid, failed_files

def update_checksum_for_file(file_path: Path, algorithm: str = "sha256", checksum_file: Optional[Path] = None) -> bool:
    """
    Compute checksum for a single file and update the global checksums.txt.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        checksum_file: Path to checksums file.
        
    Returns:
        True if successful, False otherwise.
    """
    if checksum_file is None:
        checksum_file = get_project_root() / CHECKSUM_FILE
    
    # Ensure artifacts directory exists
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        checksum = compute_checksum(file_path, algorithm)
        rel_path = str(file_path.relative_to(get_project_root()))
        
        # Load existing checksums
        existing = {}
        if checksum_file.exists():
            with open(checksum_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        existing[parts[1]] = parts[0]
        
        # Update or add
        existing[rel_path] = checksum
        
        # Write back
        with open(checksum_file, "w") as f:
            f.write(f"# Checksums for project artifacts (Generated by checksum_utils)\n")
            f.write(f"# Format: <hash>  <relative_path>\n")
            for path, hash_val in existing.items():
                f.write(f"{hash_val}  {path}\n")
        
        logger.info(f"Updated checksum for {rel_path} in {checksum_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update checksum for {file_path}: {e}")
        return False

def main():
    """CLI entry point for checksum operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage file checksums for data integrity.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate checksums for specified files")
    gen_parser.add_argument("files", nargs="+", help="Files to checksum")
    gen_parser.add_argument("-a", "--algorithm", default="sha256", choices=["md5", "sha256"], help="Hash algorithm")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify files against checksums.txt")
    verify_parser.add_argument("-a", "--algorithm", default="sha256", choices=["md5", "sha256"], help="Hash algorithm")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update checksum for a single file")
    update_parser.add_argument("file", help="File to update checksum for")
    update_parser.add_argument("-a", "--algorithm", default="sha256", choices=["md5", "sha256"], help="Hash algorithm")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        files = [get_project_root() / f for f in args.files]
        checksums = generate_checksums(files, args.algorithm)
        if checksums:
            logger.info(f"Generated checksums for {len(checksums)} files.")
        else:
            logger.warning("No checksums generated.")
            
    elif args.command == "verify":
        valid, failed = verify_checksums(algorithm=args.algorithm)
        if valid:
            logger.info("All checksums verified successfully.")
        else:
            logger.error(f"Verification failed for {len(failed)} files: {failed}")
            exit(1)
            
    elif args.command == "update":
        file_path = get_project_root() / args.file
        if update_checksum_for_file(file_path, args.algorithm):
            logger.info("Checksum updated successfully.")
        else:
            logger.error("Failed to update checksum.")
            exit(1)
            
    else:
        parser.print_help()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
