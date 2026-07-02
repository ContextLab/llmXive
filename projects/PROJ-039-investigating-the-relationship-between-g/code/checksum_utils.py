"""
Checksum verification utilities for data integrity.

Provides MD5 and SHA256 checksum generation and verification
to enforce the artifacts/checksums.txt protocol.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from config import get_project_root

# Configure logger for this module
logger = logging.getLogger(__name__)

def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use ('md5' or 'sha256').
        
    Returns:
        Hexadecimal digest string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is specified.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'md5' or 'sha256'.")
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for checksum: {e}")
        raise

def generate_checksums(
    file_paths: List[Path], 
    output_path: Path, 
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Generate checksums for multiple files and write them to a protocol file.
    
    The output format is: <hash>  <relative_path>
    
    Args:
        file_paths: List of file paths to checksum.
        output_path: Path where the checksums.txt file will be written.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    project_root = get_project_root()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f_out:
        for file_path in file_paths:
            if not file_path.exists():
                logger.warning(f"Skipping non-existent file: {file_path}")
                continue
            
            try:
                checksum = compute_checksum(file_path, algorithm)
                # Store relative path for portability
                rel_path = file_path.relative_to(project_root)
                checksums[str(rel_path)] = checksum
                
                # Write in standard checksum format: hash  filename
                f_out.write(f"{checksum}  {rel_path}\n")
                logger.info(f"Generated {algorithm} checksum for {rel_path}")
            except Exception as e:
                logger.error(f"Failed to generate checksum for {file_path}: {e}")
    
    return checksums

def verify_checksums(
    checksum_file_path: Path, 
    algorithm: str = "sha256", 
    strict: bool = True
) -> Tuple[bool, Dict[str, str]]:
    """
    Verify file checksums against a stored checksums file.
    
    Args:
        checksum_file_path: Path to the checksums.txt file.
        algorithm: Expected hash algorithm.
        strict: If True, return False if any file is missing or mismatched.
                If False, only report mismatches but don't fail on missing files.
                
    Returns:
        Tuple of (all_valid, failed_files_dict).
        failed_files_dict maps relative paths to error messages.
    """
    if not checksum_file_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file_path}")
    
    all_valid = True
    failed_files = {}
    project_root = get_project_root()
    
    with open(checksum_file_path, "r", encoding="utf-8") as f_in:
        for line_num, line in enumerate(f_in, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Parse standard checksum format: <hash>  <filename>
            parts = line.split("  ", 1)
            if len(parts) != 2:
                logger.warning(f"Invalid checksum line format at line {line_num}: {line}")
                continue
            
            expected_hash, rel_path = parts
            file_path = project_root / rel_path
            
            if not file_path.exists():
                msg = f"File not found: {file_path}"
                failed_files[rel_path] = msg
                logger.error(msg)
                if strict:
                    all_valid = False
                continue
            
            try:
                actual_hash = compute_checksum(file_path, algorithm)
                if actual_hash.lower() != expected_hash.lower():
                    msg = f"Checksum mismatch for {rel_path}"
                    failed_files[rel_path] = msg
                    logger.error(msg)
                    if strict:
                        all_valid = False
                else:
                    logger.debug(f"Checksum verified for {rel_path}")
            except Exception as e:
                msg = f"Error verifying {rel_path}: {e}"
                failed_files[rel_path] = msg
                logger.error(msg)
                if strict:
                    all_valid = False
    
    return all_valid, failed_files

def update_checksum_for_file(
    file_path: Path, 
    checksum_file_path: Path, 
    algorithm: str = "sha256"
) -> bool:
    """
    Update the checksum for a specific file in the checksums file.
    If the file exists in the checksums file, update its entry.
    If not, append it.
    
    Args:
        file_path: Path to the file whose checksum needs updating.
        checksum_file_path: Path to the checksums file.
        algorithm: Hash algorithm to use.
        
    Returns:
        True if successful, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"Cannot update checksum: file not found {file_path}")
        return False
    
    project_root = get_project_root()
    rel_path = file_path.relative_to(project_root)
    
    try:
        new_checksum = compute_checksum(file_path, algorithm)
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return False
    
    # Read existing lines
    lines = []
    if checksum_file_path.exists():
        with open(checksum_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    # Find and replace or append
    updated = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        
        parts = stripped.split("  ", 1)
        if len(parts) == 2 and parts[1] == str(rel_path):
            # Update this line
            new_lines.append(f"{new_checksum}  {rel_path}\n")
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        # Append new entry
        new_lines.append(f"{new_checksum}  {rel_path}\n")
    
    # Write back
    with open(checksum_file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    logger.info(f"Updated checksum for {rel_path}")
    return True

def main():
    """
    Command-line interface for checksum operations.
    Usage:
      python code/checksum_utils.py generate <file_pattern>
      python code/checksum_utils.py verify
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code/checksum_utils.py <generate|verify> [args]")
        sys.exit(1)
    
    command = sys.argv[1]
    checksum_file = get_project_root() / "artifacts" / "checksums.txt"
    
    if command == "generate":
        if len(sys.argv) < 3:
            print("Usage: python code/checksum_utils.py generate <file_pattern>")
            sys.exit(1)
        
        pattern = sys.argv[2]
        # Simple glob implementation for the pattern
        # For simplicity, we assume the pattern is a relative path or simple glob
        # In a real scenario, use pathlib.Path.glob()
        matching_files = []
        base_dir = get_project_root()
        
        # Handle simple cases: data/processed/*.csv, etc.
        if "*" in pattern:
            # Find the directory part
            dir_part = pattern.split("*")[0].rstrip("/")
            base = base_dir / dir_part if dir_part else base_dir
            if base.exists():
                for f in base.glob(pattern.split("*")[1].lstrip("/")):
                    if f.is_file():
                        matching_files.append(f)
        else:
            full_path = base_dir / pattern
            if full_path.exists() and full_path.is_file():
                matching_files.append(full_path)
        
        if not matching_files:
            print(f"No files found matching: {pattern}")
            sys.exit(1)
        
        generate_checksums(matching_files, checksum_file)
        print(f"Checksums written to {checksum_file}")
    
    elif command == "verify":
        try:
            all_valid, failed = verify_checksums(checksum_file)
            if all_valid:
                print("All checksums verified successfully.")
                sys.exit(0)
            else:
                print("Checksum verification failed:")
                for path, error in failed.items():
                    print(f"  - {path}: {error}")
                sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
